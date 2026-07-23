"""discount coupons + order discount fields

Revision ID: 0004_coupons
Revises: 0003_merchant
Create Date: 2026-07-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_coupons"
down_revision = "0003_merchant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "coupons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False, unique=True),
        sa.Column("kind", sa.String(10), nullable=False, server_default="percent"),
        sa.Column("value", sa.Numeric(12, 2), nullable=False),
        sa.Column("min_order", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("max_uses", sa.Integer()),
        sa.Column("used_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_coupons_code", "coupons", ["code"], unique=True)

    op.add_column("orders", sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("orders", sa.Column("coupon_code", sa.String(40)))


def downgrade() -> None:
    op.drop_column("orders", "coupon_code")
    op.drop_column("orders", "discount_amount")
    op.drop_table("coupons")
