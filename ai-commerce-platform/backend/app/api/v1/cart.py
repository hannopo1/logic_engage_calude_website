from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional
from app.core.database import get_db
from app.models.user import User
from app.schemas.cart import CartItemIn, CartItemUpdate, CartOut
from app.services import cart_service

router = APIRouter()


def _resolve(db, user, session_id):
    return cart_service.get_or_create_cart(db, user, session_id)


@router.get("", response_model=CartOut)
def get_cart(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
) -> dict:
    cart = _resolve(db, user, x_session_id)
    return cart_service.serialize_cart(cart)


@router.post("/items", response_model=CartOut)
def add_to_cart(
    payload: CartItemIn,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
) -> dict:
    cart = _resolve(db, user, x_session_id)
    cart = cart_service.add_item(db, cart, payload.product_id, payload.quantity)
    return cart_service.serialize_cart(cart)


@router.patch("/items/{product_id}", response_model=CartOut)
def update_cart_item(
    product_id: int,
    payload: CartItemUpdate,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
) -> dict:
    cart = _resolve(db, user, x_session_id)
    cart = cart_service.update_item(db, cart, product_id, payload.quantity)
    return cart_service.serialize_cart(cart)


@router.delete("/items/{product_id}", response_model=CartOut)
def remove_cart_item(
    product_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
) -> dict:
    cart = _resolve(db, user, x_session_id)
    cart = cart_service.remove_item(db, cart, product_id)
    return cart_service.serialize_cart(cart)
