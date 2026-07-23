"""merchant console: product fulfillment_type + analytics events

Revision ID: 0003_merchant
Revises: 0002_dropshipping
Create Date: 2026-07-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_merchant"
down_revision = "0002_dropshipping"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("fulfillment_type", sa.String(20), nullable=False, server_default="dropship"),
    )

    op.create_table(
        "analytics_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("session_id", sa.String(80)),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("path", sa.String(300)),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="SET NULL")),
        sa.Column("query", sa.String(300)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_analytics_events_event_type", "analytics_events", ["event_type"])
    op.create_index("ix_analytics_events_session_id", "analytics_events", ["session_id"])
    op.create_index("ix_analytics_events_created_at", "analytics_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("analytics_events")
    op.drop_column("products", "fulfillment_type")
