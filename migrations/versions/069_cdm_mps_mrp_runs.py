"""Spec 029 — MPS/MRP durable run snapshots.

Revision ID: 069
Revises: 068
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "069"
down_revision = "068"
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
        "cdm_mps_run",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(64), nullable=False),
        sa.Column("run_payload", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_mps_run_tenant_created", "cdm_mps_run", ["tenant_id", "created_at"])
    _rls("cdm_mps_run")

    op.create_table(
        "cdm_mrp_run",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("root_product_id", sa.String(64), nullable=False),
        sa.Column("run_payload", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_mrp_run_tenant_created", "cdm_mrp_run", ["tenant_id", "created_at"])
    _rls("cdm_mrp_run")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_mrp_run")
    op.drop_table("cdm_mrp_run")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_mps_run")
    op.drop_table("cdm_mps_run")
