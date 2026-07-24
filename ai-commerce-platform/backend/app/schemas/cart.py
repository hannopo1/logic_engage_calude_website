from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.catalog import ProductOut


class CartItemIn(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=0)  # 0 removes the line


class CartItemOut(BaseModel):
    id: int
    product: ProductOut
    quantity: int
    line_total: Decimal


class CartOut(BaseModel):
    id: int
    items: list[CartItemOut]
    subtotal: Decimal
    item_count: int
