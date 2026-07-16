"""Phase 6A — A14 Analytics Intelligence: auto-generated insights.

Revision ID: 061
Revises: 060
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "061"
down_revision = "060"
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
        "cdm_analytics_insight",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("insight_code", sa.String(40), nullable=True),
        sa.Column("category", sa.String(40), nullable=True),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("detail", sa.Text, nullable=True),
        sa.Column("severity", sa.String(16), server_default="info"),
        sa.Column("confidence", sa.Numeric(4, 2), server_default="0"),
        sa.Column("suggested_action", sa.Text, nullable=True),
        sa.Column("evidence", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("acknowledged", sa.Boolean, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_analytics_insight_tenant", "cdm_analytics_insight", ["tenant_id", "created_at"])
    _rls("cdm_analytics_insight")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_analytics_insight")
    op.drop_table("cdm_analytics_insight")
