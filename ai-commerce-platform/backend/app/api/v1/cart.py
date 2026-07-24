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
    """Resolve the cart associated with a user or session.
    
    Parameters:
        db: The database session.
        user: The optional authenticated user.
        session_id: The optional session identifier.
    
    Returns:
        The existing or newly created cart.
    """
    return cart_service.get_or_create_cart(db, user, session_id)


@router.get("", response_model=CartOut)
def get_cart(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
) -> dict:
    """
    Retrieve the current shopping cart for an authenticated user or session.
    
    Parameters:
        x_session_id (str | None): Optional session identifier used to associate the cart with a guest session.
    
    Returns:
        dict: The serialized shopping cart.
    """
    cart = _resolve(db, user, x_session_id)
    return cart_service.serialize_cart(cart)


@router.post("/items", response_model=CartOut)
def add_to_cart(
    payload: CartItemIn,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
) -> dict:
    """
    Add a product to the current user's or session's cart.
    
    Parameters:
        payload (CartItemIn): Product identifier and quantity to add.
    
    Returns:
        dict: The updated serialized cart.
    """
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
    """
    Update the quantity of a product in the cart.
    
    Parameters:
        product_id (int): Identifier of the product to update.
        payload (CartItemUpdate): Updated item quantity.
    
    Returns:
        dict: The serialized cart after updating the item.
    """
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
    """
    Remove a product from the current shopping cart.
    
    Parameters:
        product_id (int): Identifier of the product to remove.
    
    Returns:
        dict: The updated serialized shopping cart.
    """
    cart = _resolve(db, user, x_session_id)
    cart = cart_service.remove_item(db, cart, product_id)
    return cart_service.serialize_cart(cart)
