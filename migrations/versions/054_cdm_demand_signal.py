"""Phase 3 — Multi-source demand fusion signals.

Revision ID: 054
Revises: 053
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "054"
down_revision = "053"
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
        "cdm_demand_signal",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", UUID, nullable=True),
        sa.Column("product_code", sa.String(100), nullable=True),
        sa.Column("horizon_days", sa.Integer, nullable=False, server_default="28"),
        sa.Column("fused_qty", sa.Numeric(14, 2), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("confidence_label", sa.String(20), nullable=False),
        sa.Column("seasonal_factor", sa.Numeric(8, 4), server_default="1"),
        sa.Column("signals", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("explanation", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_demand_signal_tenant_product",
        "cdm_demand_signal",
        ["tenant_id", "product_id", "created_at"],
    )
    _rls("cdm_demand_signal")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_demand_signal")
    op.drop_table("cdm_demand_signal")
