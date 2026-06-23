"""Add disruption_event, duration_prediction tables + AI schedule columns

Revision ID: 004
Revises: 003
Create Date: 2026-06-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade():
    # cdm_disruption_event
    op.create_table(
        "cdm_disruption_event",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mo_id", UUID, sa.ForeignKey("cdm_manufacturing_order.id")),
        sa.Column("work_order_id", UUID),
        sa.Column("work_center_id", UUID, sa.ForeignKey("cdm_work_center.id")),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("metadata", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_disruption_detected", "cdm_disruption_event", ["tenant_id", "detected_at"])

    # cdm_duration_prediction
    op.create_table(
        "cdm_duration_prediction",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mo_id", UUID, sa.ForeignKey("cdm_manufacturing_order.id")),
        sa.Column("work_order_id", UUID),
        sa.Column("actual_duration_mins", sa.Numeric(10, 2)),
        sa.Column("predicted_duration_mins", sa.Numeric(10, 2), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4)),
        sa.Column("fallback_used", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_duration_prediction_mo", "cdm_duration_prediction", ["tenant_id", "mo_id"])

    # AI schedule columns on manufacturing_order
    op.add_column("cdm_manufacturing_order", sa.Column("ai_suggested_start", sa.DateTime(timezone=True)))
    op.add_column("cdm_manufacturing_order", sa.Column("ai_suggested_end", sa.DateTime(timezone=True)))
    op.add_column("cdm_manufacturing_order", sa.Column("ai_schedule_version", sa.Integer, server_default=sa.text("0")))
    op.add_column("cdm_manufacturing_order", sa.Column("active_schedule_id", UUID))
    op.add_column("cdm_manufacturing_order", sa.Column(
        "disruption_status", sa.String(20), nullable=False, server_default="none"
    ))
    op.create_check_constraint(
        "ck_mo_disruption_status",
        "cdm_manufacturing_order",
        "disruption_status IN ('none','impacted','resolved')",
    )

    # Frozen horizon support on work_order
    op.add_column("cdm_work_order", sa.Column("is_frozen", sa.Boolean, nullable=False, server_default=sa.text("false")))
    op.add_column("cdm_work_order", sa.Column("frozen_at", sa.DateTime(timezone=True)))


def downgrade():
    op.drop_column("cdm_work_order", "frozen_at")
    op.drop_column("cdm_work_order", "is_frozen")
    op.drop_constraint("ck_mo_disruption_status", "cdm_manufacturing_order")
    op.drop_column("cdm_manufacturing_order", "disruption_status")
    op.drop_column("cdm_manufacturing_order", "active_schedule_id")
    op.drop_column("cdm_manufacturing_order", "ai_schedule_version")
    op.drop_column("cdm_manufacturing_order", "ai_suggested_end")
    op.drop_column("cdm_manufacturing_order", "ai_suggested_start")
    op.drop_table("cdm_duration_prediction")
    op.drop_table("cdm_disruption_event")
