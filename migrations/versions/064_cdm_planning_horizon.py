"""Phase 7 §1 — Multi-Horizon Planning: horizon snapshots + cascade log.

Revision ID: 064
Revises: 063
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "064"
down_revision = "063"
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
        "cdm_planning_horizon",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("horizon", sa.String(20), nullable=False),  # strategic/tactical/operational
        sa.Column("coverage_pct", sa.Numeric(6, 2), server_default="0"),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("pending_decisions", sa.Integer, server_default="0"),
        sa.Column("metrics", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_planning_horizon_tenant", "cdm_planning_horizon", ["tenant_id", "captured_at"]
    )
    _rls("cdm_planning_horizon")

    op.create_table(
        "cdm_horizon_cascade",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),  # down/up
        sa.Column("driver", sa.Text, nullable=True),
        sa.Column("payload", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("board_decision_required", sa.Boolean, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_horizon_cascade_tenant", "cdm_horizon_cascade", ["tenant_id", "created_at"]
    )
    _rls("cdm_horizon_cascade")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_horizon_cascade")
    op.drop_table("cdm_horizon_cascade")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_planning_horizon")
    op.drop_table("cdm_planning_horizon")
