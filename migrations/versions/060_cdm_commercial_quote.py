"""Phase 6A — A13 Commercial Intelligence: pricing/deal/contract snapshots.

Revision ID: 060
Revises: 059
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "060"
down_revision = "059"
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
        "cdm_commercial_quote",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_id", sa.String(80), nullable=True),
        sa.Column("product_id", sa.String(80), nullable=True),
        sa.Column("customer_id", sa.String(80), nullable=True),
        sa.Column("customer_tier", sa.String(4), nullable=True),
        sa.Column("list_price", sa.Numeric(14, 2), server_default="0"),
        sa.Column("recommended_price", sa.Numeric(14, 2), server_default="0"),
        sa.Column("total_discount_pct", sa.Numeric(6, 2), server_default="0"),
        sa.Column("margin_pct", sa.Numeric(6, 2), server_default="0"),
        sa.Column("within_floor", sa.Boolean, server_default=sa.text("true")),
        sa.Column("requires_approval", sa.Boolean, server_default=sa.text("false")),
        sa.Column("deal_profitability", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("contract_compliance", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_commercial_quote_tenant", "cdm_commercial_quote", ["tenant_id", "created_at"])
    _rls("cdm_commercial_quote")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_commercial_quote")
    op.drop_table("cdm_commercial_quote")
