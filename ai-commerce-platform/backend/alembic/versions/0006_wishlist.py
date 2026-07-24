"""wishlist items

Revision ID: 0006_wishlist
Revises: 0005_reviews
Create Date: 2026-07-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_wishlist"
down_revision = "0005_reviews"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the wishlist_items table (one row per user/product)."""
    op.create_table(
        "wishlist_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "product_id", name="uq_wishlist_user_product"),
    )
    op.create_index("ix_wishlist_items_user_id", "wishlist_items", ["user_id"])


def downgrade() -> None:
    """Drop the wishlist_items table and its index."""
    op.drop_index("ix_wishlist_items_user_id", table_name="wishlist_items")
    op.drop_table("wishlist_items")
