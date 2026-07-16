"""Phase 7 §3 — Demand collaboration consensus + bias tracking.

Revision ID: 066
Revises: 065
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "066"
down_revision = "065"
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
        "cdm_demand_consensus",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product", sa.String(80), nullable=True),
        sa.Column("period", sa.String(20), nullable=True),
        sa.Column("statistical_baseline", sa.Numeric(12, 2), server_default="0"),
        sa.Column("consensus_units", sa.Numeric(12, 2), server_default="0"),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("contributions", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("disagreement_flags", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("bias_tracking", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_demand_consensus_tenant", "cdm_demand_consensus", ["tenant_id", "created_at"]
    )
    _rls("cdm_demand_consensus")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_demand_consensus")
    op.drop_table("cdm_demand_consensus")
