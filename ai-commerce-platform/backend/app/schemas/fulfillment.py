from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ---------- Suppliers ----------

class SupplierIn(BaseModel):
    name: str
    slug: str
    kind: str = "marketplace"          # marketplace | classifieds
    region: str = "EG"
    mode: str = "assisted"             # manual | assisted | api
    website: str | None = None
    notes: str | None = None
    is_active: bool = True


class SupplierPatch(BaseModel):
    name: str | None = None
    kind: str | None = None
    mode: str | None = None
    website: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class SupplierOut(BaseModel):
    id: int
    name: str
    slug: str
    kind: str
    region: str
    mode: str
    website: str | None = None
    notes: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}


# ---------- Supplier offers ----------

class OfferIn(BaseModel):
    product_id: int
    supplier_id: int
    url: str | None = None
    external_sku: str | None = None
    supplier_price: Decimal
    shipping_cost: Decimal = Decimal("0")
    currency: str = "EGP"
    lead_time_days: int = 3
    is_active: bool = True


class OfferPatch(BaseModel):
    url: str | None = None
    external_sku: str | None = None
    supplier_price: Decimal | None = None
    shipping_cost: Decimal | None = None
    lead_time_days: int | None = None
    is_active: bool | None = None


class OfferOut(BaseModel):
    id: int
    product_id: int
    supplier_id: int
    url: str | None = None
    external_sku: str | None = None
    supplier_price: Decimal
    shipping_cost: Decimal
    currency: str
    lead_time_days: int
    is_active: bool

    model_config = {"from_attributes": True}


# ---------- Purchase orders ----------

class POEventOut(BaseModel):
    status: str
    note: str | None = None
    actor: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PurchaseOrderOut(BaseModel):
    id: int
    order_id: int
    order_item_id: int
    supplier_offer_id: int | None = None
    status: str
    quantity: int
    expected_cost: Decimal | None = None
    actual_cost: Decimal | None = None
    supplier_order_ref: str | None = None
    tracking_no: str | None = None
    carrier: str | None = None
    created_at: datetime
    # denormalized for the operator dashboard
    product_name: str | None = None
    supplier_name: str | None = None
    supplier_url: str | None = None
    customer_address: str | None = None
    selling_total: Decimal | None = None
    events: list[POEventOut] = []


class RejectIn(BaseModel):
    note: str = Field(min_length=2, description="سبب الرفض")
    cancel: bool = False  # true → cancel outright; false → back to pending_sourcing


class MarkPurchasedIn(BaseModel):
    supplier_order_ref: str = Field(min_length=1)
    actual_cost: Decimal | None = None


class ShipIn(BaseModel):
    tracking_no: str = Field(min_length=1)
    carrier: str | None = None


class DashboardOut(BaseModel):
    po_counts: dict[str, int]
    orders_today: int
    revenue_total: Decimal
    expected_cost_open: Decimal
    estimated_margin_percent: float | None = None


# ---------- Customer-facing timeline (sanitized) ----------

class TimelineStep(BaseModel):
    status: str          # internal status key (for the UI stepper)
    label: str           # Arabic customer-facing label
    at: datetime | None = None
    done: bool
