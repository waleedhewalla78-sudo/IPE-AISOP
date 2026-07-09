"""Migration 038 — Sprint 7 cross-tool activity events (EIB activity store)."""

from alembic import op

revision = "038"
down_revision = "037"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS cdm_activity_event (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id),
            source_tool VARCHAR(64) NOT NULL,
            event_type VARCHAR(128) NOT NULL,
            actor_id VARCHAR(128),
            entity_type VARCHAR(64),
            entity_id UUID,
            summary TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}',
            severity VARCHAR(16) NOT NULL DEFAULT 'info',
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            idempotency_key VARCHAR(256),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_activity_idempotency
        ON cdm_activity_event (tenant_id, idempotency_key)
        WHERE idempotency_key IS NOT NULL
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_activity_tenant_occurred
        ON cdm_activity_event (tenant_id, occurred_at DESC)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_activity_tenant_source
        ON cdm_activity_event (tenant_id, source_tool, occurred_at DESC)
    """)
    op.execute("ALTER TABLE cdm_activity_event ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_activity_event")
    op.execute("""
        CREATE POLICY tenant_isolation ON cdm_activity_event
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    """)


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_activity_event")
    op.execute("DROP TABLE IF EXISTS cdm_activity_event")
