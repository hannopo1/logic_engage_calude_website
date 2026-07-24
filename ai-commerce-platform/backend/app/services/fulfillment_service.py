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
    """
    Determine whether a purchase order can move between statuses.
    
    Parameters:
        current (str): The purchase order's current status.
        target (str): The proposed next status.
    
    Returns:
        bool: `true` if the transition is allowed, `false` otherwise.
    """
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
    """
    Move a purchase order to a new status and synchronize its parent order.
    
    Parameters:
        target (str): The status to assign to the purchase order.
        actor (str): The actor recorded for the status-change event.
        note (str | None): Optional note recorded with the event.
        commit (bool): Whether to commit the transaction and refresh the purchase order.
    
    Returns:
        PurchaseOrder: The updated purchase order.
    
    Raises:
        HTTPException: If the target status is unknown or the transition is not allowed.
    """
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
    """
    Record an informational event for a purchase order without changing its status.
    
    Parameters:
        note (str): Description of the event.
        actor (str): Identifier of the event source.
        commit (bool): Whether to commit the database transaction immediately.
    """
    db.add(PurchaseOrderEvent(purchase_order_id=po.id, status=po.status, note=note, actor=actor))
    if commit:
        db.commit()


def sync_order_status(db: Session, order_id: int) -> None:
    """
    Synchronize the customer-facing order status with the aggregate progress of its purchase orders.
    
    Cancelled and failed purchase orders are excluded from progress calculations. An order with no active purchase orders is marked as cancelled; otherwise, its status reflects whether all active purchase orders are delivered, all are shipped or delivered, any has progressed beyond sourcing, or all remain pending. Cash-on-delivery orders are marked as paid when all active purchase orders are delivered.
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
