"""Add cdm_chaos_cost_snapshot for V6-R5 cost-of-chaos rollups

Revision ID: 027
Revises: 026
Create Date: 2026-06-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "027"
down_revision = "026"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cdm_chaos_cost_snapshot",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("cdm_tenant.id"), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("total_chaos_usd", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("categories", JSONB, nullable=False, server_default="[]"),
        sa.Column("top_mos", JSONB, nullable=False, server_default="[]"),
        sa.Column("war_room_links", JSONB, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_chaos_cost_snapshot_tenant_date",
        "cdm_chaos_cost_snapshot",
        ["tenant_id", "snapshot_date"],
        unique=True,
    )

    op.execute("ALTER TABLE cdm_chaos_cost_snapshot ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON cdm_chaos_cost_snapshot "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)"
    )


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_chaos_cost_snapshot")
    op.execute("ALTER TABLE cdm_chaos_cost_snapshot DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_chaos_cost_snapshot_tenant_date", table_name="cdm_chaos_cost_snapshot")
    op.drop_table("cdm_chaos_cost_snapshot")
