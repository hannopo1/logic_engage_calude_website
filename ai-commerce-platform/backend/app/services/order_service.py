"""Checkout: turn a cart into an order, decrementing stock atomically."""
from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.cart import Cart
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User


def create_order_from_cart(
    db: Session, cart: Cart, user: User | None, shipping_address: str | None
) -> Order:
    if not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Validate stock before committing anything.
    for it in cart.items:
        if it.product.stock_qty < it.quantity:
            raise HTTPException(
                status_code=409,
                detail=f"Insufficient stock for '{it.product.name}' (have {it.product.stock_qty}).",
            )

    total = Decimal("0")
    order = Order(
        user_id=user.id if user else None,
        status="pending",
        payment_status="unpaid",
        total_amount=Decimal("0"),
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
        # Decrement stock (MVP inventory movement).
        product: Product = it.product
        product.stock_qty -= it.quantity

    order.total_amount = total

    # Empty the cart now that it has been converted.
    for it in list(cart.items):
        db.delete(it)

    db.commit()
    db.refresh(order)
    return order
