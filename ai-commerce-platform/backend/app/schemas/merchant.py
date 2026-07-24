from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ---------- Product management (admin) ----------

class ProductIn(BaseModel):
    name: str
    slug: str | None = None  # auto-derived from name if omitted
    description: str | None = None
    price: Decimal
    cost_price: Decimal | None = None
    sku: str | None = None
    stock_qty: int = 0
    image: str | None = None
    tags: str | None = None
    category_id: int | None = None
    fulfillment_type: str = "dropship"  # dropship | own_stock
    seo_title: str | None = None
    is_active: bool = True


class ProductPatch(BaseModel):
    name: str | None = None
    description: str | None = None
    price: Decimal | None = None
    cost_price: Decimal | None = None
    stock_qty: int | None = None
    image: str | None = None
    tags: str | None = None
    category_id: int | None = None
    fulfillment_type: str | None = None
    is_active: bool | None = None


class ProductAdminOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None = None
    price: Decimal
    cost_price: Decimal | None = None
    sku: str | None = None
    stock_qty: int
    image: str | None = None
    tags: str | None = None
    category_id: int | None = None
    fulfillment_type: str
    is_active: bool
    offer_count: int = 0

    model_config = {"from_attributes": True}


# ---------- Customers (admin) ----------

class CustomerOut(BaseModel):
    id: int
    email: str
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    created_at: datetime
    order_count: int = 0
    total_spent: Decimal = Decimal("0")


# ---------- Analytics ----------

class EventIn(BaseModel):
    event_type: str = Field(description="page_view|product_view|search|add_to_cart|begin_checkout|purchase")
    path: str | None = None
    product_id: int | None = None
    query: str | None = None


class FunnelStep(BaseModel):
    key: str
    label: str
    count: int


class TopItem(BaseModel):
    label: str
    count: int


class AnalyticsOut(BaseModel):
    days: int
    unique_visitors: int
    page_views: int
    product_views: int
    searches: int
    add_to_cart: int
    orders: int
    conversion_rate: float  # orders / unique_visitors %
    funnel: list[FunnelStep]
    top_products: list[TopItem]
    top_searches: list[TopItem]
    daily_visitors: list[TopItem]  # label = date, count = unique sessions
