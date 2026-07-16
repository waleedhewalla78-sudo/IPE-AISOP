"""Phase 6C — A17 Cross-Functional Orchestrator: decisions + policy gate.

Revision ID: 063
Revises: 062
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "063"
down_revision = "062"
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
        "cdm_orchestrator_decision",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scenario", sa.String(60), nullable=True),
        sa.Column("order_id", sa.String(80), nullable=True),
        sa.Column("decision", sa.String(40), nullable=True),
        sa.Column("governance_level", sa.SmallInteger, server_default="1"),
        sa.Column("policy_gate", sa.String(16), nullable=True),
        sa.Column("coordinated_agents", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("rationale", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("policies", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("reversible", sa.Boolean, server_default=sa.text("true")),
        sa.Column("reversal_window_hours", sa.SmallInteger, server_default="4"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_orchestrator_decision_tenant", "cdm_orchestrator_decision", ["tenant_id", "created_at"])
    _rls("cdm_orchestrator_decision")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_orchestrator_decision")
    op.drop_table("cdm_orchestrator_decision")
