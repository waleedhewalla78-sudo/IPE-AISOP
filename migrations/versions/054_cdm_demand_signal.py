"""Phase 3 — Multi-source demand FUSION results.

Conflict note: Table name `cdm_demand_signal` already exists (pre-054) as a
raw signal-ingest ledger (source_type/signal_ts/value). Tech Spec §1.2 lists
054 CREATE `cdm_demand_signal` for fused forecasts. We create
`cdm_demand_fusion` for fused outputs to avoid breaking the ingest schema.

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
    op.execute("""
        CREATE TABLE IF NOT EXISTS cdm_demand_fusion (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
            product_id UUID NULL,
            product_code VARCHAR(100) NULL,
            horizon_days INTEGER NOT NULL DEFAULT 28,
            fused_qty NUMERIC(14, 2) NOT NULL,
            confidence NUMERIC(5, 4) NOT NULL,
            confidence_label VARCHAR(20) NOT NULL,
            seasonal_factor NUMERIC(8, 4) DEFAULT 1,
            signals JSONB DEFAULT '[]'::jsonb,
            explanation TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_demand_fusion_tenant_product
        ON cdm_demand_fusion (tenant_id, product_id, created_at)
    """)
    _rls("cdm_demand_fusion")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_demand_fusion")
    op.execute("DROP TABLE IF EXISTS cdm_demand_fusion")
