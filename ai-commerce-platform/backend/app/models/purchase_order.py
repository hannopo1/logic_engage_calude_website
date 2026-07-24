from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# Canonical PO statuses. Transition rules live in services/fulfillment_service.py.
PO_STATUSES = (
    "pending_sourcing",   # no viable supplier offer yet — operator attention
    "awaiting_approval",  # agent picked an offer, waiting for operator approval
    "purchasing",         # approved; assisted-mode purchase package issued
    "purchased",          # placed at the supplier (ref recorded)
    "shipped",            # supplier shipped to the customer (tracking recorded)
    "delivered",          # customer received the item
    "failed",
    "cancelled",
)


class PurchaseOrder(Base):
    """One drop-ship purchase: buy `quantity` of an order item from a supplier
    and ship it straight to the customer's address (kept on the parent order)."""

    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False)
    supplier_offer_id: Mapped[int | None] = mapped_column(ForeignKey("supplier_offers.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(30), default="pending_sourcing", nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_cost: Mapped[float | None] = mapped_column(Numeric(12, 2))  # landed cost * qty at sourcing time
    actual_cost: Mapped[float | None] = mapped_column(Numeric(12, 2))    # what we really paid
    supplier_order_ref: Mapped[str | None] = mapped_column(String(160))
    tracking_no: Mapped[str | None] = mapped_column(String(160))
    carrier: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    order = relationship("Order")
    order_item = relationship("OrderItem")
    offer = relationship("SupplierOffer")
    events: Mapped[list["PurchaseOrderEvent"]] = relationship(
        back_populates="purchase_order", cascade="all, delete-orphan", order_by="PurchaseOrderEvent.id"
    )


class PurchaseOrderEvent(Base):
    """Append-only audit trail for a PO: who moved it, to what, and why."""

    __tablename__ = "purchase_order_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    actor: Mapped[str] = mapped_column(String(20), default="system", nullable=False)  # agent|operator|system
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    purchase_order: Mapped["PurchaseOrder"] = relationship(back_populates="events")
