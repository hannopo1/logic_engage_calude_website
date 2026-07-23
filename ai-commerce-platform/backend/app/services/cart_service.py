"""Cart resolution and mutation logic, shared by the cart & order routers."""
from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.user import User


def get_or_create_cart(db: Session, user: User | None, session_id: str | None) -> Cart:
    """Resolve the active cart for a user (preferred) or an anonymous session."""
    if user is not None:
        cart = db.scalar(select(Cart).where(Cart.user_id == user.id))
        if cart is None:
            cart = Cart(user_id=user.id)
            db.add(cart)
            db.commit()
            db.refresh(cart)
        return cart

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide an X-Session-Id header for anonymous carts, or log in.",
        )
    cart = db.scalar(select(Cart).where(Cart.session_id == session_id))
    if cart is None:
        cart = Cart(session_id=session_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def add_item(db: Session, cart: Cart, product_id: int, quantity: int) -> Cart:
    product = db.get(Product, product_id)
    if product is None or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")

    item = db.scalar(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
    )
    if item is None:
        item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        db.add(item)
    else:
        item.quantity += quantity
    db.commit()
    db.refresh(cart)
    return cart


def update_item(db: Session, cart: Cart, product_id: int, quantity: int) -> Cart:
    item = db.scalar(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Item not in cart")
    if quantity == 0:
        db.delete(item)
    else:
        item.quantity = quantity
    db.commit()
    db.refresh(cart)
    return cart


def remove_item(db: Session, cart: Cart, product_id: int) -> Cart:
    item = db.scalar(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
    )
    if item is not None:
        db.delete(item)
        db.commit()
        db.refresh(cart)
    return cart


def serialize_cart(cart: Cart) -> dict:
    """Shape a Cart ORM object into the CartOut response payload."""
    items = []
    subtotal = Decimal("0")
    count = 0
    for it in cart.items:
        line_total = Decimal(str(it.product.price)) * it.quantity
        subtotal += line_total
        count += it.quantity
        items.append({"id": it.id, "product": it.product, "quantity": it.quantity, "line_total": line_total})
    return {"id": cart.id, "items": items, "subtotal": subtotal, "item_count": count}
