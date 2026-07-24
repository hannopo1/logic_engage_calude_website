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
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder, PurchaseOrderEvent
from app.models.supplier import Supplier, SupplierOffer


def landed_cost(offer: SupplierOffer) -> Decimal:
    """
    Calculate the total landed cost of a supplier offer.
    
    Parameters:
    	offer (SupplierOffer): The supplier offer whose supplier price and shipping cost are combined.
    
    Returns:
    	Decimal: The supplier price plus the shipping cost.
    """
    return Decimal(str(offer.supplier_price)) + Decimal(str(offer.shipping_cost))


def margin_percent(selling_price: Decimal, cost: Decimal) -> Decimal:
    """
    Calculate the gross margin percentage for a selling price and cost.
    
    Parameters:
    	selling_price (Decimal): The item's selling price.
    	cost (Decimal): The item's cost.
    
    Returns:
    	Decimal: Zero when the selling price is less than or equal to zero; otherwise, the gross margin percentage.
    """
    if selling_price <= 0:
        return Decimal("0")
    return (selling_price - cost) / selling_price * 100


def pick_offer(
    db: Session, product_id: int, selling_unit_price: Decimal
) -> tuple[SupplierOffer | None, str]:
    """
    Selects the cheapest active supplier offer that meets the minimum margin requirement.
    
    Parameters:
    	db (Session): Database session used to retrieve supplier offers.
    	product_id (int): Identifier of the product to source.
    	selling_unit_price (Decimal): Unit price charged to the customer.
    
    Returns:
    	tuple[SupplierOffer | None, str]: The selected offer and an Arabic status message. Returns `None` with a reason when no active offer exists or no offer meets the minimum margin.
    """
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
    """
    Create purchase orders for the order's eligible items.
    
    Parameters:
    	db (Session): Database session used to load order items and persist purchase orders.
    	order (Order): Order whose items require fulfillment sourcing.
    	commit (bool): Whether to commit the transaction after processing all items.
    
    Returns:
    	list[PurchaseOrder]: Purchase orders created for the order's items.
    """
    created: list[PurchaseOrder] = []
    items = list(db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)))
    for item in items:
        if item.product_id is None:
            continue

        # Own-inventory items skip supplier sourcing: the merchant already holds
        # the stock, so the PO is created ready to ship (no supplier, no buy step).
        product = db.get(Product, item.product_id)
        if product is not None and product.fulfillment_type == "own_stock":
            cost = (
                Decimal(str(product.cost_price)) * item.quantity
                if product.cost_price is not None
                else None
            )
            po = PurchaseOrder(
                order_id=order.id,
                order_item_id=item.id,
                status="purchased",  # from own stock → ready to ship
                quantity=item.quantity,
                expected_cost=cost,
                actual_cost=cost,
            )
            db.add(po)
            db.flush()
            db.add(
                PurchaseOrderEvent(
                    purchase_order_id=po.id,
                    status="purchased",
                    note="من مخزونك الخاص — جاهز للشحن مباشرة",
                    actor="agent",
                )
            )
            created.append(po)
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
