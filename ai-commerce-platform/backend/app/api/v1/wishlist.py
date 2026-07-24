"""Customer wishlist: save products to revisit or buy later. Auth required."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.product import Product
from app.models.user import User
from app.models.wishlist import WishlistItem
from app.schemas.catalog import ProductOut

router = APIRouter()


@router.get("", response_model=list[ProductOut])
def list_wishlist(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ProductOut]:
    """Products the current user saved, newest first."""
    products = db.scalars(
        select(Product)
        .join(WishlistItem, WishlistItem.product_id == Product.id)
        .where(WishlistItem.user_id == user.id)
        .order_by(WishlistItem.id.desc())
    )
    return [ProductOut.model_validate(p) for p in products]


@router.post("/{product_id}", response_model=ProductOut, status_code=201)
def add_wishlist(
    product_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProductOut:
    """Add a product to the wishlist (idempotent — repeat adds are a no-op)."""
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")
    exists = db.scalar(
        select(WishlistItem).where(
            WishlistItem.user_id == user.id, WishlistItem.product_id == product_id
        )
    )
    if exists is None:
        db.add(WishlistItem(user_id=user.id, product_id=product_id))
        db.commit()
    return ProductOut.model_validate(product)


@router.delete("/{product_id}")
def remove_wishlist(
    product_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Remove a product from the wishlist (idempotent)."""
    item = db.scalar(
        select(WishlistItem).where(
            WishlistItem.user_id == user.id, WishlistItem.product_id == product_id
        )
    )
    if item is not None:
        db.delete(item)
        db.commit()
    return {"removed": True}
