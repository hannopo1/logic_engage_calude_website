"""Sourcing agent — runs automatically on every new order.

For each order item it selects the cheapest active supplier offer whose landed
cost still leaves at least MARGIN_MIN_PERCENT gross margin against our selling
price, then opens a purchase order awaiting operator approval. Items with no
viable offer get a `pending_sourcing` PO so the operator queue surfaces them.
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.order import Order, OrderItem
from app.models.purchase_order import PurchaseOrder, PurchaseOrderEvent
from app.models.supplier import Supplier, SupplierOffer


def landed_cost(offer: SupplierOffer) -> Decimal:
    return Decimal(str(offer.supplier_price)) + Decimal(str(offer.shipping_cost))


def margin_percent(selling_price: Decimal, cost: Decimal) -> Decimal:
    if selling_price <= 0:
        return Decimal("0")
    return (selling_price - cost) / selling_price * 100


def pick_offer(
    db: Session, product_id: int, selling_unit_price: Decimal
) -> tuple[SupplierOffer | None, str]:
    """Cheapest active offer meeting the margin threshold. Returns (offer, reason)."""
    offers = list(
        db.scalars(
            select(SupplierOffer)
            .join(Supplier, Supplier.id == SupplierOffer.supplier_id)
            .where(
                SupplierOffer.product_id == product_id,
                SupplierOffer.is_active.is_(True),
                Supplier.is_active.is_(True),
            )
        )
    )
    if not offers:
        return None, "لا توجد عروض توريد نشطة لهذا المنتج"

    viable = [
        o
        for o in offers
        if margin_percent(selling_unit_price, landed_cost(o)) >= Decimal(str(settings.MARGIN_MIN_PERCENT))
    ]
    if not viable:
        best = min(offers, key=landed_cost)
        pct = margin_percent(selling_unit_price, landed_cost(best)).quantize(Decimal("0.1"))
        return None, (
            f"أفضل عرض متاح يحقق هامش {pct}% فقط "
            f"(الحد الأدنى {settings.MARGIN_MIN_PERCENT}%) — يحتاج قرار مشغّل"
        )

    chosen = min(viable, key=landed_cost)
    pct = margin_percent(selling_unit_price, landed_cost(chosen)).quantize(Decimal("0.1"))
    return chosen, f"اختير أرخص مورد يحقق الهامش: هامش متوقع {pct}%"


def source_order(db: Session, order: Order, *, commit: bool = True) -> list[PurchaseOrder]:
    """Create one PO per order item. Called right after checkout."""
    created: list[PurchaseOrder] = []
    items = list(db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)))
    for item in items:
        if item.product_id is None:
            continue
        offer, reason = pick_offer(db, item.product_id, Decimal(str(item.unit_price)))
        if offer is not None:
            po = PurchaseOrder(
                order_id=order.id,
                order_item_id=item.id,
                supplier_offer_id=offer.id,
                status="awaiting_approval",
                quantity=item.quantity,
                expected_cost=landed_cost(offer) * item.quantity,
            )
            db.add(po)
            db.flush()
            db.add(
                PurchaseOrderEvent(
                    purchase_order_id=po.id,
                    status="awaiting_approval",
                    note=reason,
                    actor="agent",
                )
            )
        else:
            po = PurchaseOrder(
                order_id=order.id,
                order_item_id=item.id,
                status="pending_sourcing",
                quantity=item.quantity,
            )
            db.add(po)
            db.flush()
            db.add(
                PurchaseOrderEvent(
                    purchase_order_id=po.id,
                    status="pending_sourcing",
                    note=reason,
                    actor="agent",
                )
            )
        created.append(po)
    if commit:
        db.commit()
    return created
