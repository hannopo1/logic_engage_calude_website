from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CouponIn(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    kind: str = "percent"  # percent | fixed
    value: Decimal
    min_order: Decimal = Decimal("0")
    max_uses: int | None = None
    is_active: bool = True
    expires_at: datetime | None = None


class CouponPatch(BaseModel):
    kind: str | None = None
    value: Decimal | None = None
    min_order: Decimal | None = None
    max_uses: int | None = None
    is_active: bool | None = None
    expires_at: datetime | None = None


class CouponOut(BaseModel):
    id: int
    code: str
    kind: str
    value: Decimal
    min_order: Decimal
    max_uses: int | None = None
    used_count: int
    is_active: bool
    expires_at: datetime | None = None

    model_config = {"from_attributes": True}


class CouponValidateIn(BaseModel):
    code: str
    subtotal: Decimal


class CouponValidateOut(BaseModel):
    code: str
    kind: str
    discount: Decimal
    new_total: Decimal
