from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Supplier(Base):
    """An external source we drop-ship from (marketplace or classifieds).

    `mode` controls how the purchasing agent may execute against it:
      - manual:   operator does everything by hand (e.g. OLX person-to-person)
      - assisted: agent prepares the full purchase package, operator confirms
      - api:      an official API connector is configured (see app/agents/connectors.py)
    """

    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(20), default="marketplace", nullable=False)  # marketplace|classifieds
    region: Mapped[str] = mapped_column(String(10), default="EG", nullable=False)
    mode: Mapped[str] = mapped_column(String(20), default="assisted", nullable=False)  # manual|assisted|api
    website: Mapped[str | None] = mapped_column(String(300))
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SupplierOffer(Base):
    """A concrete sourcing option: this product, at this supplier, at this cost.

    Landed cost = supplier_price + shipping_cost; the sourcing agent picks the
    cheapest active offer that still meets the margin threshold.
    """

    __tablename__ = "supplier_offers"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id", ondelete="CASCADE"), index=True, nullable=False)
    url: Mapped[str | None] = mapped_column(String(600))
    external_sku: Mapped[str | None] = mapped_column(String(120))
    supplier_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    shipping_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="EGP", nullable=False)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    supplier: Mapped["Supplier"] = relationship()
    product = relationship("Product")
