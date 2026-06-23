"""Add financial projection table

Revision ID: 011
Revises: 010
Create Date: 2026-06-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cdm_financial_projection",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("mo_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("product_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("projection_type", sa.String(50), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="0"),
        sa.Column("unit_cost", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("total_cost", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("revenue", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("margin", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("margin_pct", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("labor_cost", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("material_cost", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("energy_cost", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("overhead_cost", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("wip_value", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("projection_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
    )


def downgrade():
    op.drop_table("cdm_financial_projection")
