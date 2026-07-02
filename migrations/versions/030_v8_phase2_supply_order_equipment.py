"""v8 Phase 2: customer orders, supply plans, equipment assets

Revision ID: 030
Revises: 029
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "030"
down_revision = "029"
branch_labels = None
depends_on = None


def _rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY tenant_isolation ON {table} "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)"
    )


def upgrade():
    op.create_table(
        "cdm_customer_order",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", UUID, sa.ForeignKey("cdm_customer.id")),
        sa.Column("order_number", sa.String(64), nullable=False),
        sa.Column("order_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("requested_date", sa.DateTime(timezone=True)),
        sa.Column("promised_date", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(24), server_default="open"),
        sa.Column("priority", sa.Integer, server_default="3"),
        sa.Column("total_value", sa.Numeric(14, 2), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_customer_order_tenant_status", "cdm_customer_order", ["tenant_id", "status"])
    _rls("cdm_customer_order")

    op.create_table(
        "cdm_customer_order_line",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_id", UUID, sa.ForeignKey("cdm_customer_order.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", UUID, sa.ForeignKey("cdm_product.id"), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("promised_quantity", sa.Numeric(14, 4)),
        sa.Column("unit_price", sa.Numeric(14, 4), server_default="0"),
        sa.Column("line_status", sa.String(24), server_default="open"),
    )
    op.create_index("ix_customer_order_line_order", "cdm_customer_order_line", ["order_id"])
    _rls("cdm_customer_order_line")

    op.create_table(
        "cdm_order_promise",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_line_id", UUID, sa.ForeignKey("cdm_customer_order_line.id", ondelete="CASCADE"), nullable=False),
        sa.Column("facility_id", UUID),
        sa.Column("promise_type", sa.String(8), nullable=False),
        sa.Column("promise_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confidence_score", sa.Numeric(5, 4), server_default="0.85"),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_order_promise_line", "cdm_order_promise", ["order_line_id"])
    _rls("cdm_order_promise")

    op.create_table(
        "cdm_supply_plan",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("horizon_days", sa.Integer, server_default="30"),
        sa.Column("status", sa.String(24), server_default="draft"),
        sa.Column("plan_jsonb", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_supply_plan_tenant", "cdm_supply_plan", ["tenant_id", "status"])
    _rls("cdm_supply_plan")

    op.create_table(
        "cdm_equipment_asset",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("work_center_id", UUID, sa.ForeignKey("cdm_work_center.id")),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("asset_type", sa.String(64), server_default="machine"),
        sa.Column("location", sa.String(128)),
        sa.Column("install_date", sa.DateTime(timezone=True)),
        sa.Column("specs_jsonb", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("health_score", sa.Numeric(5, 2), server_default="100"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_equipment_asset_tenant", "cdm_equipment_asset", ["tenant_id", "name"])
    _rls("cdm_equipment_asset")


def downgrade():
    op.drop_table("cdm_equipment_asset")
    op.drop_table("cdm_supply_plan")
    op.drop_table("cdm_order_promise")
    op.drop_table("cdm_customer_order_line")
    op.drop_table("cdm_customer_order")
