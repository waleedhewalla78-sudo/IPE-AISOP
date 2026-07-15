"""Phase 3 — 5-why root cause chain storage.

Revision ID: 056
Revises: 055
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "056"
down_revision = "055"
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
        "cdm_root_cause_chain",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mo_id", UUID, nullable=False),
        sa.Column("analysis_date", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("chain_depth", sa.Integer, nullable=False),
        sa.Column("chain_data", JSONB, nullable=False),
        sa.Column("root_cause_type", sa.String(50), nullable=True),
        sa.Column("root_cause_entity_type", sa.String(50), nullable=True),
        sa.Column("root_cause_entity_id", UUID, nullable=True),
        sa.Column("root_cause_description", sa.Text, nullable=True),
        sa.Column("recommendations", JSONB, nullable=True),
        sa.Column("acknowledged", sa.Boolean, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_root_cause_tenant_mo", "cdm_root_cause_chain", ["tenant_id", "mo_id"])
    _rls("cdm_root_cause_chain")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_root_cause_chain")
    op.drop_table("cdm_root_cause_chain")
