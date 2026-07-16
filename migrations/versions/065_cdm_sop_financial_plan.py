"""Phase 7 §2 — Financial S&OP plan rows (volume + P&L per consensus).

Revision ID: 065
Revises: 064
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "065"
down_revision = "064"
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
        "cdm_sop_financial_plan",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product", sa.String(80), nullable=True),
        sa.Column("period", sa.String(20), nullable=True),
        sa.Column("consensus_demand", sa.Numeric(12, 2), server_default="0"),
        sa.Column("constrained_supply", sa.Numeric(12, 2), server_default="0"),
        sa.Column("revenue_usd", sa.Numeric(16, 2), server_default="0"),
        sa.Column("gross_profit_usd", sa.Numeric(16, 2), server_default="0"),
        sa.Column("margin_pct", sa.Numeric(6, 2), server_default="0"),
        sa.Column("margin_below_floor", sa.Boolean, server_default=sa.text("false")),
        sa.Column("finance_alerts", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_sop_financial_plan_tenant", "cdm_sop_financial_plan", ["tenant_id", "created_at"]
    )
    _rls("cdm_sop_financial_plan")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_sop_financial_plan")
    op.drop_table("cdm_sop_financial_plan")
