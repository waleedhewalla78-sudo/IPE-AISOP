"""Add S&OP forecast and plan tables

Revision ID: 016
Revises: 015
Create Date: 2026-06-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cdm_sop_forecast",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("product_family", sa.String(100), nullable=False, index=True),
        sa.Column("period_type", sa.String(20), nullable=False, server_default="weekly"),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("forecast_qty", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("actual_qty", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("capacity_qty", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("unit", sa.String(20), nullable=False, server_default="units"),
        sa.Column("source", sa.String(50), nullable=False, server_default="pipeline"),
        sa.Column("confidence_pct", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "cdm_sop_plan",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("plan_name", sa.String(200), nullable=False),
        sa.Column("horizon_weeks", sa.Integer, nullable=False, server_default="52"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("alpha", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("plan_data", JSON, nullable=True),
        sa.Column("gap_analysis", JSON, nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
    )

    op.execute(
        "CREATE POLICY tenant_isolation ON cdm_sop_forecast "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)"
    )
    op.execute(
        "CREATE POLICY tenant_isolation ON cdm_sop_plan "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)"
    )


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_sop_plan")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_sop_forecast")
    op.drop_table("cdm_sop_plan")
    op.drop_table("cdm_sop_forecast")