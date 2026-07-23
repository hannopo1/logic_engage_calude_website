from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Coupon(Base):
    """A discount code applied at checkout.

    `kind`:
      percent → `value` is a percentage off the subtotal (0-100)
      fixed   → `value` is a flat EGP amount off
    Validity is gated by is_active, expires_at, min_order, and max_uses.
    """

    __tablename__ = "coupons"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(10), default="percent", nullable=False)  # percent | fixed
    value: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    min_order: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    max_uses: Mapped[int | None] = mapped_column(Integer)  # None = unlimited
    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
