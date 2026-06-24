"""Add activity cost drivers for V6 activity-based planning

Revision ID: 024
Revises: 023
Create Date: 2026-06-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "024"
down_revision = "023"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cdm_activity_cost_drivers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("cdm_tenant.id"), nullable=False, index=True),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("cdm_product.id"), nullable=True),
        sa.Column("setup_mins", sa.Numeric(10, 2), nullable=False, server_default="15"),
        sa.Column("overtime_rate_usd_per_hr", sa.Numeric(12, 4), nullable=False, server_default="95"),
        sa.Column("expedite_cost_per_unit", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("overhead_pct", sa.Numeric(6, 4), nullable=False, server_default="0.12"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_activity_cost_drivers_tenant_product",
        "cdm_activity_cost_drivers",
        ["tenant_id", "product_id"],
    )

    op.execute("ALTER TABLE cdm_activity_cost_drivers ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON cdm_activity_cost_drivers "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)"
    )


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_activity_cost_drivers")
    op.drop_index("ix_activity_cost_drivers_tenant_product", table_name="cdm_activity_cost_drivers")
    op.drop_table("cdm_activity_cost_drivers")
