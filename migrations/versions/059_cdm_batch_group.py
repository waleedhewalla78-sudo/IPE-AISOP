"""Phase 3 — Smart batching results.

Revision ID: 059
Revises: 058
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "059"
down_revision = "058"
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
        "cdm_batch_group",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("work_centre_id", UUID, nullable=True),
        sa.Column("work_centre_name", sa.String(100), nullable=True),
        sa.Column("original_sequence", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("optimised_sequence", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("original_changeover_min", sa.Numeric(10, 2), server_default="0"),
        sa.Column("optimised_changeover_min", sa.Numeric(10, 2), server_default="0"),
        sa.Column("savings_min", sa.Numeric(10, 2), server_default="0"),
        sa.Column("savings_pct", sa.Numeric(6, 2), server_default="0"),
        sa.Column("delivery_dates_maintained", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_batch_group_tenant", "cdm_batch_group", ["tenant_id", "created_at"])
    _rls("cdm_batch_group")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_batch_group")
    op.drop_table("cdm_batch_group")
