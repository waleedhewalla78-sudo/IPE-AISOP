"""Phase 6B — A15 Procurement Execution: 3-way match results.

Revision ID: 062
Revises: 061
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "062"
down_revision = "061"
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
        "cdm_three_way_match",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("po_id", sa.String(80), nullable=True),
        sa.Column("invoice_id", sa.String(80), nullable=True),
        sa.Column("invoice_total", sa.Numeric(14, 2), server_default="0"),
        sa.Column("all_matched", sa.Boolean, server_default=sa.text("false")),
        sa.Column("routing", sa.String(40), nullable=True),
        sa.Column("lines", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("exceptions", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_three_way_match_tenant", "cdm_three_way_match", ["tenant_id", "created_at"])
    _rls("cdm_three_way_match")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_three_way_match")
    op.drop_table("cdm_three_way_match")
