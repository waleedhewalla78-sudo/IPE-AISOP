"""Migration 040 — Sprint S8 tenant health snapshots for multi-tenant ops."""

from alembic import op

revision = "040"
down_revision = "039"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS cdm_tenant_health (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
            health_status VARCHAR(16) NOT NULL DEFAULT 'unknown',
            sync_status VARCHAR(16) NOT NULL DEFAULT 'unknown',
            last_sync_at TIMESTAMPTZ,
            failed_sync_count_24h INTEGER NOT NULL DEFAULT 0,
            mdr_passed BOOLEAN,
            mdr_score_pct NUMERIC(5, 2),
            active_mo_count INTEGER NOT NULL DEFAULT 0,
            open_alert_count INTEGER NOT NULL DEFAULT 0,
            snapshot_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, snapshot_at)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_tenant_health_tenant_snapshot
        ON cdm_tenant_health (tenant_id, snapshot_at DESC)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_tenant_health_status
        ON cdm_tenant_health (health_status, snapshot_at DESC)
    """)
    op.execute("ALTER TABLE cdm_tenant_health ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_tenant_health")
    op.execute("""
        CREATE POLICY tenant_isolation ON cdm_tenant_health
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    """)


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_tenant_health")
    op.execute("DROP TABLE IF EXISTS cdm_tenant_health")
