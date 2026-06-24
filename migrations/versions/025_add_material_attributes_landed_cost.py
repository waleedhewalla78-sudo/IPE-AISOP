"""Add material attributes and landed cost profiles for V6-R2

Revision ID: 025
Revises: 024
Create Date: 2026-06-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "025"
down_revision = "024"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cdm_material_attributes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("cdm_tenant.id"), nullable=False, index=True),
        sa.Column("material_id", UUID(as_uuid=True), sa.ForeignKey("cdm_product.id"), nullable=False),
        sa.Column("attributes", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_material_attributes_tenant_material",
        "cdm_material_attributes",
        ["tenant_id", "material_id"],
        unique=True,
    )

    op.create_table(
        "cdm_landed_cost_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("cdm_tenant.id"), nullable=False, index=True),
        sa.Column("supplier_id", UUID(as_uuid=True), sa.ForeignKey("cdm_supplier.id"), nullable=True),
        sa.Column("region", sa.String(64), nullable=False),
        sa.Column("base_cost_usd", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("freight_usd", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("tariff_pct", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column("risk_premium_pct", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_landed_cost_profiles_tenant_region",
        "cdm_landed_cost_profiles",
        ["tenant_id", "region"],
    )

    op.execute("ALTER TABLE cdm_material_attributes ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON cdm_material_attributes "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)"
    )
    op.execute("ALTER TABLE cdm_landed_cost_profiles ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON cdm_landed_cost_profiles "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)"
    )


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_landed_cost_profiles")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_material_attributes")
    op.drop_index("ix_landed_cost_profiles_tenant_region", table_name="cdm_landed_cost_profiles")
    op.drop_index("ix_material_attributes_tenant_material", table_name="cdm_material_attributes")
    op.drop_table("cdm_landed_cost_profiles")
    op.drop_table("cdm_material_attributes")
