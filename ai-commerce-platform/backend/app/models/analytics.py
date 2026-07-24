from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# Event types tracked for the storefront funnel.
EVENT_TYPES = (
    "page_view",
    "product_view",
    "search",
    "add_to_cart",
    "begin_checkout",
    "purchase",
)


class AnalyticsEvent(Base):
    """A single storefront interaction, used for visitor/behavior analytics.

    Written by the public POST /events endpoint (no auth); keyed by an anonymous
    session id so guests and logged-in users are both measured.
    """

    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(80), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    path: Mapped[str | None] = mapped_column(String(300))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"))
    query: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
