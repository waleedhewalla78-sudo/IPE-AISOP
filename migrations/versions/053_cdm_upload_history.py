"""Phase 3 — File upload tracking.

Revision ID: 053
Revises: 052
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "053"
down_revision = "052"
branch_labels = None
depends_on = None


def _rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
    op.execute(
        f"""
        CREATE POLICY tenant_isolation ON {table}
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        """
    )


def upgrade():
    op.create_table(
        "cdm_upload_history",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=False),
        sa.Column("file_name", sa.String(300), nullable=False),
        sa.Column("wizard_phase", sa.Integer, nullable=True),
        sa.Column("status", sa.String(30), server_default="processing"),
        sa.Column("total_rows", sa.Integer, server_default="0"),
        sa.Column("accepted_rows", sa.Integer, server_default="0"),
        sa.Column("rejected_rows", sa.Integer, server_default="0"),
        sa.Column("warning_count", sa.Integer, server_default="0"),
        sa.Column("validation", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("agents_triggered", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("uploaded_by", UUID, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_upload_history_tenant", "cdm_upload_history", ["tenant_id", "created_at"])
    _rls("cdm_upload_history")

    op.create_table(
        "cdm_upload_error",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "upload_id",
            UUID,
            sa.ForeignKey("cdm_upload_history.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("row_number", sa.Integer, nullable=False),
        sa.Column("column_name", sa.String(100), nullable=True),
        sa.Column("raw_value", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=False),
        sa.Column("severity", sa.String(20), server_default="error"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_upload_error_upload", "cdm_upload_error", ["upload_id"])
    _rls("cdm_upload_error")

    op.create_table(
        "cdm_upload_wizard_state",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("current_phase", sa.Integer, server_default="1"),
        sa.Column("phase_status", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("agents_activated", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", name="uq_upload_wizard_tenant"),
    )
    _rls("cdm_upload_wizard_state")


def downgrade():
    for table in ("cdm_upload_wizard_state", "cdm_upload_error", "cdm_upload_history"):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.drop_table(table)
