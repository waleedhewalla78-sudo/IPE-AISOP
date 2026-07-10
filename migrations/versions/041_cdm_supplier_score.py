"""Migration 041 — Sprint S10 supplier risk score history."""

from alembic import op

revision = "041"
down_revision = "040"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS cdm_supplier_score (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
            supplier_id UUID NOT NULL REFERENCES cdm_supplier(id) ON DELETE CASCADE,
            reliability_score NUMERIC(5, 4) NOT NULL,
            risk_tier VARCHAR(16) NOT NULL DEFAULT 'medium',
            on_time_pct NUMERIC(5, 2),
            avg_delay_days NUMERIC(6, 2),
            sample_size INTEGER NOT NULL DEFAULT 0,
            contributing_factors JSONB NOT NULL DEFAULT '{}',
            scored_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_supplier_score_tenant_supplier
        ON cdm_supplier_score (tenant_id, supplier_id, scored_at DESC)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_supplier_score_risk_tier
        ON cdm_supplier_score (tenant_id, risk_tier)
    """)
    op.execute("ALTER TABLE cdm_supplier_score ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_supplier_score")
    op.execute("""
        CREATE POLICY tenant_isolation ON cdm_supplier_score
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    """)


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_supplier_score")
    op.execute("DROP TABLE IF EXISTS cdm_supplier_score")
