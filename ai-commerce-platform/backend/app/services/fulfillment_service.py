"""Purchase-order state machine + order-status synchronization.

Single owner of PO transition rules. Everything that moves a PO — agents and
admin endpoints alike — must go through `transition()` so the audit trail and
the parent order's status stay consistent.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.purchase_order import PO_STATUSES, PurchaseOrder, PurchaseOrderEvent

# Allowed transitions: current -> set of next statuses.
_TRANSITIONS: dict[str, set[str]] = {
    "pending_sourcing": {"awaiting_approval", "cancelled"},
    "awaiting_approval": {"purchasing", "purchased", "pending_sourcing", "cancelled"},
    "purchasing": {"purchased", "failed", "cancelled"},
    "purchased": {"shipped", "failed"},
    "shipped": {"delivered", "failed"},
    "delivered": set(),
    "failed": {"pending_sourcing", "cancelled"},   # retry path
    "cancelled": set(),
}


def can_transition(current: str, target: str) -> bool:
    return target in _TRANSITIONS.get(current, set())


def transition(
    db: Session,
    po: PurchaseOrder,
    target: str,
    *,
    actor: str,
    note: str | None = None,
    commit: bool = True,
) -> PurchaseOrder:
    """Move a PO to `target`, record the audit event, sync the parent order."""
    if target not in PO_STATUSES:
        raise HTTPException(status_code=400, detail=f"Unknown status '{target}'")
    if not can_transition(po.status, target):
        raise HTTPException(
            status_code=409,
            detail=f"Illegal transition {po.status} → {target}",
        )
    po.status = target
    db.add(PurchaseOrderEvent(purchase_order_id=po.id, status=target, note=note, actor=actor))
    sync_order_status(db, po.order_id)
    if commit:
        db.commit()
        db.refresh(po)
    return po


def record_event(
    db: Session, po: PurchaseOrder, note: str, *, actor: str = "system", commit: bool = True
) -> None:
    """Append an informational event without changing status."""
    db.add(PurchaseOrderEvent(purchase_order_id=po.id, status=po.status, note=note, actor=actor))
    if commit:
        db.commit()


def sync_order_status(db: Session, order_id: int) -> None:
    """Reflect PO progress onto the customer-facing order status.

    completed  — every PO delivered
    shipped    — every PO at least shipped
    processing — at least one PO past approval (purchasing/purchased/…)
    pending    — otherwise (sourcing / awaiting approval)
    Cancelled/failed POs are excluded from the "all" aggregates so one refunded
    line doesn't block the rest of the order.
    """
    order = db.get(Order, order_id)
    if order is None:
        return
    pos = list(db.scalars(select(PurchaseOrder).where(PurchaseOrder.order_id == order_id)))
    if not pos:
        return
    active = [p for p in pos if p.status not in ("cancelled", "failed")]
    if not active:
        order.status = "cancelled"
        return
    if all(p.status == "delivered" for p in active):
        order.status = "completed"
        # COD: cash is collected on delivery.
        if order.payment_method == "cod":
            order.payment_status = "paid"
    elif all(p.status in ("shipped", "delivered") for p in active):
        order.status = "shipped"
    elif any(p.status in ("purchasing", "purchased", "shipped", "delivered") for p in active):
        order.status = "processing"
    else:
        order.status = "pending"
