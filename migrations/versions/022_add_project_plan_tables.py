"""Add project plan upload and version tables

Revision ID: 022
Revises: 021
Create Date: 2026-06-22
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cdm_project_plan",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_code", sa.String(64), nullable=False),
        sa.Column("plan_name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("active_version_id", UUID),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "plan_code", name="uq_project_plan_tenant_code"),
    )

    op.create_table(
        "cdm_project_plan_version",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", UUID, sa.ForeignKey("cdm_project_plan.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("file_name", sa.String(512), nullable=False),
        sa.Column("file_size_bytes", sa.Integer, nullable=False),
        sa.Column("file_sha256", sa.String(64), nullable=False),
        sa.Column("uploaded_by", UUID),
        sa.Column("upload_notes", sa.Text),
        sa.Column("operations", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("validation_summary", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("plan_id", "version_number", name="uq_project_plan_version_number"),
    )

    op.create_foreign_key(
        "fk_project_plan_active_version",
        "cdm_project_plan",
        "cdm_project_plan_version",
        ["active_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("idx_project_plan_tenant", "cdm_project_plan", ["tenant_id"])
    op.create_index("idx_project_plan_version_plan", "cdm_project_plan_version", ["plan_id", "is_active"])


def downgrade():
    op.drop_constraint("fk_project_plan_active_version", "cdm_project_plan", type_="foreignkey")
    op.drop_index("idx_project_plan_version_plan", table_name="cdm_project_plan_version")
    op.drop_index("idx_project_plan_tenant", table_name="cdm_project_plan")
    op.drop_table("cdm_project_plan_version")
    op.drop_table("cdm_project_plan")
