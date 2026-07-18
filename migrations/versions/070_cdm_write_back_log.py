"""Spec 030 / Phase 8 — Odoo write-back safety log.

Revision ID: 070
Revises: 069
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "070"
down_revision = "069"
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
        "cdm_write_back_log",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(128), nullable=False),
        sa.Column("field_name", sa.String(128), nullable=True),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("action", sa.String(64), nullable=False, server_default="update"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending_approval"),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("approved_by", sa.String(128), nullable=True),
        sa.Column("requested_by", sa.String(128), nullable=True),
        sa.Column("financial_impact", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", JSONB, nullable=True),
        sa.Column("is_live", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rollback_deadline", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_write_back_log_tenant_created",
        "cdm_write_back_log",
        ["tenant_id", "created_at"],
    )
    op.create_index(
        "ix_write_back_log_entity",
        "cdm_write_back_log",
        ["tenant_id", "entity_type", "entity_id"],
    )
    _rls("cdm_write_back_log")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_write_back_log")
    op.drop_table("cdm_write_back_log")
