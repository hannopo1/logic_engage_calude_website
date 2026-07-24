"""product reviews (verified purchase + moderation)

Revision ID: 0005_reviews
Revises: 0004_coupons
Create Date: 2026-07-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_reviews"
down_revision = "0004_coupons"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create the reviews table and its product index.
    """
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="SET NULL")),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(120)),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("product_id", "user_id", name="uq_review_product_user"),
    )
    op.create_index("ix_reviews_product_id", "reviews", ["product_id"])


def downgrade() -> None:
    """
    Remove the reviews table and its associated product index.
    """
    op.drop_index("ix_reviews_product_id", table_name="reviews")
    op.drop_table("reviews")
