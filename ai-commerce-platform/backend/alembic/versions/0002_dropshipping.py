"""drop-shipping: suppliers, offers, purchase orders + Arabic-friendly search

Revision ID: 0002_dropshipping
Revises: 0001_init
Create Date: 2026-07-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_dropshipping"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- payment method on orders (COD-first launch) ---
    """
    Apply the database schema changes required for dropshipping workflows.
    
    Adds order payment method support, creates supplier, supplier offer, purchase order, and purchase order event tables, and configures Arabic-friendly full-text search for products.
    """
    op.add_column(
        "orders",
        sa.Column("payment_method", sa.String(20), nullable=False, server_default="cod"),
    )

    # --- suppliers ---
    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("slug", sa.String(180), nullable=False, unique=True),
        sa.Column("kind", sa.String(20), nullable=False, server_default="marketplace"),
        sa.Column("region", sa.String(10), nullable=False, server_default="EG"),
        sa.Column("mode", sa.String(20), nullable=False, server_default="assisted"),
        sa.Column("website", sa.String(300)),
        sa.Column("notes", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_suppliers_slug", "suppliers", ["slug"], unique=True)

    # --- supplier offers (sourcing options per product) ---
    op.create_table(
        "supplier_offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(600)),
        sa.Column("external_sku", sa.String(120)),
        sa.Column("supplier_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("shipping_cost", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="EGP"),
        sa.Column("lead_time_days", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("last_checked_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_supplier_offers_product_id", "supplier_offers", ["product_id"])
    op.create_index("ix_supplier_offers_supplier_id", "supplier_offers", ["supplier_id"])

    # --- purchase orders ---
    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_item_id", sa.Integer(), sa.ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_offer_id", sa.Integer(), sa.ForeignKey("supplier_offers.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending_sourcing"),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("expected_cost", sa.Numeric(12, 2)),
        sa.Column("actual_cost", sa.Numeric(12, 2)),
        sa.Column("supplier_order_ref", sa.String(160)),
        sa.Column("tracking_no", sa.String(160)),
        sa.Column("carrier", sa.String(120)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_purchase_orders_order_id", "purchase_orders", ["order_id"])
    op.create_index("ix_purchase_orders_status", "purchase_orders", ["status"])

    # --- PO audit trail ---
    op.create_table(
        "purchase_order_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "purchase_order_id",
            sa.Integer(),
            sa.ForeignKey("purchase_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("actor", sa.String(20), nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_purchase_order_events_purchase_order_id", "purchase_order_events", ["purchase_order_id"]
    )

    # --- Arabic-friendly full-text search ---
    # 'english' config stems/filters English; 'simple' tokenizes neutrally, which
    # is what we want for an Arabic catalog. Recreate the generated column + GIN.
    op.execute("DROP INDEX IF EXISTS ix_products_search_vector")
    op.execute("ALTER TABLE products DROP COLUMN search_vector")
    op.execute(
        """
        ALTER TABLE products
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            to_tsvector('simple',
                coalesce(name, '') || ' ' ||
                coalesce(description, '') || ' ' ||
                coalesce(tags, ''))
        ) STORED
        """
    )
    op.execute("CREATE INDEX ix_products_search_vector ON products USING GIN (search_vector)")


def downgrade() -> None:
    """
    Revert the dropshipping schema changes and restore the original product search configuration.
    """
    op.execute("DROP INDEX IF EXISTS ix_products_search_vector")
    op.execute("ALTER TABLE products DROP COLUMN search_vector")
    op.execute(
        """
        ALTER TABLE products
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            to_tsvector('english',
                coalesce(name, '') || ' ' ||
                coalesce(description, '') || ' ' ||
                coalesce(tags, ''))
        ) STORED
        """
    )
    op.execute("CREATE INDEX ix_products_search_vector ON products USING GIN (search_vector)")
    op.drop_table("purchase_order_events")
    op.drop_table("purchase_orders")
    op.drop_table("supplier_offers")
    op.drop_table("suppliers")
    op.drop_column("orders", "payment_method")
