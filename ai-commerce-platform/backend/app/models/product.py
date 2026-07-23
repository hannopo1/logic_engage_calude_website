from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Computed, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(280), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    cost_price: Mapped[float | None] = mapped_column(Numeric(12, 2))
    sku: Mapped[str | None] = mapped_column(String(80), unique=True)
    stock_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    image: Mapped[str | None] = mapped_column(String(500))
    tags: Mapped[str | None] = mapped_column(String(500))  # comma-separated, used by recommender
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    seo_title: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Populated by a Postgres STORED generated column (migrations 0001/0002).
    # Declared Computed so the ORM never tries to INSERT/UPDATE it.
    # 'simple' config = neutral tokenizer, Arabic-friendly.
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('simple', "
            "coalesce(name, '') || ' ' || "
            "coalesce(description, '') || ' ' || "
            "coalesce(tags, ''))",
            persisted=True,
        ),
    )

    category: Mapped["Category | None"] = relationship()
