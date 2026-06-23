"""Add plant, transfer route, and transport fleet tables for multi-plant network

Revision ID: 008
Revises: 007
Create Date: 2026-06-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "cdm_work_center",
        sa.Column("plant_id", UUID(as_uuid=True), nullable=True),
    )

    op.create_table(
        "cdm_plant",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        sa.Column("capacity_hours_per_day", sa.Float, nullable=False, server_default="8.0"),
        sa.Column("cost_per_hour", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("energy_kwh_per_hour", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("capabilities", JSON, nullable=True),
        sa.Column("metadata", JSON, nullable=True),
    )

    op.create_table(
        "cdm_transfer_route",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("origin_plant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("destination_plant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("transport_mode", sa.String(50), nullable=False, server_default="truck"),
        sa.Column("transit_time_hours", sa.Float, nullable=False, server_default="24.0"),
        sa.Column("transit_time_std_dev_hours", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("cost_per_unit", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("capacity_units", sa.Integer, nullable=True, server_default="1000"),
        sa.Column("min_batch_size", sa.Integer, nullable=True, server_default="1"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("reliability_score", sa.Float, nullable=True, server_default="0.95"),
    )

    op.create_table(
        "cdm_transport_fleet",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("route_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("vehicle_type", sa.String(50), nullable=False, server_default="truck"),
        sa.Column("capacity_units", sa.Integer, nullable=False, server_default="1000"),
        sa.Column("cost_per_trip", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("cost_per_unit", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("max_trips_per_day", sa.Integer, nullable=False, server_default="5"),
        sa.Column("available_units", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("speed_kmh", sa.Float, nullable=True, server_default="60.0"),
    )


def downgrade():
    op.drop_table("cdm_transport_fleet")
    op.drop_table("cdm_transfer_route")
    op.drop_table("cdm_plant")
    op.drop_column("cdm_work_center", "plant_id")
