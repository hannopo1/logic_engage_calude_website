"""Checkout: turn a cart into an order, then let the sourcing agent open POs.

Drop-shipping note: we hold no inventory. `stock_qty` acts as a listing
availability counter, and real fulfillment happens through purchase orders
created by the sourcing agent (app/agents/sourcing.py) in one transaction
with the order itself.
"""
from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents import sourcing
from app.models.cart import Cart
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.services import coupon_service
from app.services.payments import get_payment_provider


def create_order_from_cart(
    db: Session,
    cart: Cart,
    user: User | None,
    shipping_address: str | None,
    payment_method: str = "cod",
    coupon_code: str | None = None,
) -> Order:
    if not cart.items:
        raise HTTPException(status_code=400, detail="السلة فارغة")
    if not shipping_address or not shipping_address.strip():
        raise HTTPException(status_code=400, detail="عنوان الشحن مطلوب لإتمام الطلب")

    # Validate availability before committing anything.
    for it in cart.items:
        if it.product.stock_qty < it.quantity:
            raise HTTPException(
                status_code=409,
                detail=f"الكمية غير متاحة للمنتج '{it.product.name}' (المتاح {it.product.stock_qty}).",
            )

    subtotal = sum(Decimal(str(it.product.price)) * it.quantity for it in cart.items)

    # Optional discount coupon (validated against the subtotal).
    discount = Decimal("0")
    coupon = None
    if coupon_code and coupon_code.strip():
        coupon = coupon_service.find_valid(db, coupon_code, subtotal)
        discount = coupon_service.compute_discount(coupon, subtotal)
    payable = subtotal - discount

    # Authorize payment (COD always accepted; gateway declines until configured).
    payment = get_payment_provider(payment_method).authorize(
        float(payable), "EGP", {"user_id": user.id if user else None}
    )
    if not payment.accepted:
        raise HTTPException(status_code=402, detail=payment.detail)

    total = Decimal("0")
    order = Order(
        user_id=user.id if user else None,
        status="pending",
        payment_method=payment.method,
        payment_status=payment.status,
        total_amount=Decimal("0"),
        discount_amount=discount,
        coupon_code=coupon.code if coupon else None,
        shipping_address=shipping_address,
    )
    db.add(order)
    db.flush()  # assign order.id

    for it in cart.items:
        unit = Decimal(str(it.product.price))
        line = unit * it.quantity
        total += line
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=it.product_id,
                product_name=it.product.name,
                quantity=it.quantity,
                unit_price=unit,
                total_price=line,
            )
        )
        # Availability counter (listing-level, not warehouse stock).
        product: Product = it.product
        product.stock_qty -= it.quantity

    # Apply the discount to the order total and consume one coupon use.
    order.total_amount = max(Decimal("0"), total - discount)
    if coupon is not None:
        coupon.used_count += 1

    # Empty the cart now that it has been converted.
    for it in list(cart.items):
        db.delete(it)

    db.flush()

    # Drop-shipping: the sourcing agent opens purchase orders for every item,
    # in the same transaction as the order itself.
    sourcing.source_order(db, order, commit=False)

    db.commit()
    db.refresh(order)
    return order
