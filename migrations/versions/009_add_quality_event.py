"""Add quality event table for quality feedback loop

Revision ID: 009
Revises: 008
Create Date: 2026-06-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cdm_quality_event",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("mo_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("work_order_id", UUID(as_uuid=True), nullable=True),
        sa.Column("work_center_id", UUID(as_uuid=True), nullable=True),
        sa.Column("product_id", UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="minor"),
        sa.Column("defect_category", sa.String(100), nullable=True),
        sa.Column("defect_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("inspection_method", sa.String(50), nullable=True),
        sa.Column("root_cause", sa.String(255), nullable=True),
        sa.Column("corrective_action", sa.String(255), nullable=True),
        sa.Column("rework_required", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("rework_cycles", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_rework_cycles", sa.Integer, nullable=False, server_default="3"),
        sa.Column("scrap_quantity", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost_impact", sa.Float, nullable=True, server_default="0.0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("cdm_quality_event")
