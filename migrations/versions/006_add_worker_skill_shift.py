"""Add worker, skill, shift tables and routing operation skill requirements

Revision ID: 006
Revises: 005
Create Date: 2026-06-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade():
    # Skills table
    op.create_table(
        "cdm_skill",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.String(512)),
        sa.Column("category", sa.String(64), nullable=False, server_default="general"),
        sa.Column("certification_required", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "name", name="uq_skill_tenant_name"),
    )
    op.create_index("ix_skill_tenant", "cdm_skill", ["tenant_id"])

    # Workers table (extends Operator concept with structured skill/shift support)
    op.create_table(
        "cdm_worker",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("erp_source_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("shift_calendar_id", UUID, sa.ForeignKey("cdm_resource_calendar.id")),
        sa.Column("max_consecutive_hours", sa.Numeric(4, 2), server_default="10"),
        sa.Column("cost_per_hour", sa.Numeric(10, 2)),
        sa.Column("overtime_eligible", sa.Boolean, server_default="true"),
        sa.Column("predicted_absence_probability", sa.Numeric(5, 4)),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_worker_tenant", "cdm_worker", ["tenant_id"])
    op.create_index("ix_worker_erp", "cdm_worker", ["tenant_id", "erp_source_id"], unique=True)

    # Worker-Skill many-to-many link
    op.create_table(
        "cdm_worker_skill_link",
        sa.Column("worker_id", UUID, sa.ForeignKey("cdm_worker.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("skill_id", UUID, sa.ForeignKey("cdm_skill.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("proficiency_level", sa.SmallInteger, server_default="1"),
        sa.Column("certified_at", sa.DateTime(timezone=True)),
    )

    # Shifts table
    op.create_table(
        "cdm_shift",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.String(512)),
        sa.Column("days_of_week", JSONB, nullable=False, server_default="[0,1,2,3,4]"),
        sa.Column("start_hour", sa.Integer, nullable=False, server_default="8"),
        sa.Column("start_minute", sa.Integer, nullable=False, server_default="0"),
        sa.Column("end_hour", sa.Integer, nullable=False, server_default="16"),
        sa.Column("end_minute", sa.Integer, nullable=False, server_default="0"),
        sa.Column("break_minutes", sa.Integer, server_default="30"),
        sa.Column("timezone", sa.String(64), server_default="UTC"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_shift_tenant", "cdm_shift", ["tenant_id"])

    # Add required_skill_id and requires_operator to routing operations
    op.add_column("cdm_routing_operation", sa.Column("required_skill_id", UUID, sa.ForeignKey("cdm_skill.id")))
    op.add_column("cdm_routing_operation", sa.Column("requires_operator", sa.Boolean, server_default="true"))
    op.create_index("ix_routing_required_skill", "cdm_routing_operation", ["required_skill_id"])


def downgrade():
    op.drop_index("ix_routing_required_skill", table_name="cdm_routing_operation")
    op.drop_column("cdm_routing_operation", "requires_operator")
    op.drop_column("cdm_routing_operation", "required_skill_id")
    op.drop_table("cdm_shift")
    op.drop_table("cdm_worker_skill_link")
    op.drop_table("cdm_worker")
    op.drop_table("cdm_skill")
