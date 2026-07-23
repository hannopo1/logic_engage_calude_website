from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class OrderCreate(BaseModel):
    shipping_address: str | None = None
    payment_method: str = "cod"  # cod | gateway


class OrderItemOut(BaseModel):
    product_id: int | None = None
    product_name: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: int
    status: str
    payment_method: str = "cod"
    payment_status: str
    total_amount: Decimal
    shipping_address: str | None = None
    created_at: datetime
    items: list[OrderItemOut]

    model_config = {"from_attributes": True}
