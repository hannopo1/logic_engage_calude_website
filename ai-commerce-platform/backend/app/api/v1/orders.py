from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_optional
from app.core.database import get_db
from app.models.order import Order
from app.models.purchase_order import PurchaseOrder
from app.models.user import User
from app.schemas.fulfillment import TimelineStep
from app.schemas.order import OrderCreate, OrderOut
from app.services import cart_service, order_service

router = APIRouter()


@router.post("", response_model=OrderOut, status_code=201)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
) -> Order:
    cart = cart_service.get_or_create_cart(db, user, x_session_id)
    return order_service.create_order_from_cart(
        db, cart, user, payload.shipping_address, payload.payment_method, payload.coupon_code
    )


@router.get("", response_model=list[OrderOut])
def my_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Order]:
    return list(
        db.scalars(select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc()))
    )


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Order:
    order = db.get(Order, order_id)
    if order is None or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    return order


# Customer-facing fulfillment stages, in display order. Internal PO machinery
# (sourcing/approval/supplier identity/costs) is deliberately hidden.
_CUSTOMER_STAGES: list[tuple[str, str, set[str]]] = [
    ("placed", "تم استلام طلبك", set()),  # always done once the order exists
    ("preparing", "جارٍ تجهيز طلبك", {"purchasing", "purchased", "shipped", "delivered"}),
    ("shipped", "تم شحن طلبك", {"shipped", "delivered"}),
    ("delivered", "تم التسليم", {"delivered"}),
]


@router.get("/{order_id}/timeline", response_model=list[TimelineStep])
def order_timeline(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TimelineStep]:
    """Sanitized fulfillment timeline: what the customer sees, in Arabic."""
    order = db.get(Order, order_id)
    if order is None or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")

    pos = list(db.scalars(select(PurchaseOrder).where(PurchaseOrder.order_id == order.id)))
    active = [p for p in pos if p.status not in ("cancelled", "failed")]

    def stage_time(statuses: set[str]):
        """Latest event time at which every active PO had reached the stage."""
        times = []
        for po in active:
            hit = [e.created_at for e in po.events if e.status in statuses]
            if not hit:
                return None
            times.append(min(hit))
        return max(times) if times else None

    steps: list[TimelineStep] = [
        TimelineStep(status="placed", label="تم استلام طلبك", at=order.created_at, done=True)
    ]
    for key, label, statuses in _CUSTOMER_STAGES[1:]:
        done = bool(active) and all(po.status in statuses for po in active)
        # "preparing" counts as reached if ANY po progressed past approval
        if key == "preparing":
            done = bool(active) and any(po.status in statuses for po in active)
        steps.append(TimelineStep(status=key, label=label, at=stage_time(statuses) if done else None, done=done))
    return steps
