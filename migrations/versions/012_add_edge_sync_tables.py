"""Add edge sync tables for offline/edge gateway support

Revision ID: 012
Revises: 011
Create Date: 2026-06-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cdm_edge_gateway",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("gateway_id", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("gateway_name", sa.String(255), nullable=False),
        sa.Column("gateway_type", sa.String(50), nullable=False, server_default="standard"),
        sa.Column("plant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("api_key_hash", sa.String(255), nullable=True),
        sa.Column("mtls_cert_serial", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_status", sa.String(20), nullable=True),
        sa.Column("sync_interval_seconds", sa.Integer, nullable=False, server_default="60"),
        sa.Column("max_batch_size", sa.Integer, nullable=False, server_default="100"),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "cdm_edge_sync_batch",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("batch_id", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("gateway_id", sa.String(255), nullable=False, index=True),
        sa.Column("batch_type", sa.String(50), nullable=False),
        sa.Column("record_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("conflict_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("local_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cloud_received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "cdm_edge_sync_record",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("batch_id", sa.String(255), nullable=False, index=True),
        sa.Column("gateway_id", sa.String(255), nullable=False, index=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column("operation", sa.String(20), nullable=False),
        sa.Column("payload", JSON, nullable=False),
        sa.Column("local_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cloud_processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("conflict_status", sa.String(50), nullable=True),
        sa.Column("conflict_details", JSON, nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "cdm_edge_schedule_delta",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("gateway_id", sa.String(255), nullable=False, index=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column("delta_type", sa.String(20), nullable=False),
        sa.Column("payload", JSON, nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("checksum", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_table("cdm_edge_schedule_delta")
    op.drop_table("cdm_edge_sync_record")
    op.drop_table("cdm_edge_sync_batch")
    op.drop_table("cdm_edge_gateway")
