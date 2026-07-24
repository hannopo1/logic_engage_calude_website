from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    parent_id: int | None = None

    model_config = {"from_attributes": True}


class ProductOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None = None
    price: Decimal
    sku: str | None = None
    stock_qty: int
    image: str | None = None
    tags: str | None = None
    category_id: int | None = None
    seo_title: str | None = None
    rating_avg: float = 0.0
    rating_count: int = 0

    model_config = {"from_attributes": True}


class ProductList(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    page_size: int
