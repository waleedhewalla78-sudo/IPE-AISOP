"""Add carbon emission tracking tables

Revision ID: 010
Revises: 009
Create Date: 2026-06-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cdm_emission_factor",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("energy_source", sa.String(50), nullable=False),
        sa.Column("region", sa.String(50), nullable=False, server_default="global"),
        sa.Column("factor_kg_co2_per_kwh", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "cdm_material_carbon",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("product_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("kg_co2_per_unit", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("kg_co2_per_kg", sa.Float, nullable=True),
        sa.Column("recycled_content_pct", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("end_of_life_recyclable_pct", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("source", sa.String(50), nullable=True, server_default="estimated"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "cdm_transport_emission",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("route_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("vehicle_type", sa.String(50), nullable=False),
        sa.Column("kg_co2_per_unit_per_km", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("kg_co2_per_trip", sa.Float, nullable=True),
        sa.Column("load_factor_avg", sa.Float, nullable=True, server_default="0.8"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("cdm_transport_emission")
    op.drop_table("cdm_material_carbon")
    op.drop_table("cdm_emission_factor")
