"""Phase 3 — Capacity conflict resolution audit.

Revision ID: 058
Revises: 057
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "058"
down_revision = "057"
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
        "cdm_capacity_auction_log",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("work_centre_id", UUID, nullable=True),
        sa.Column("slot_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("winner_mo_id", UUID, nullable=True),
        sa.Column("winner_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("entries", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("reschedule_plan", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_capacity_auction_tenant", "cdm_capacity_auction_log", ["tenant_id", "created_at"])
    _rls("cdm_capacity_auction_log")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_capacity_auction_log")
    op.drop_table("cdm_capacity_auction_log")
