"""Copilot audit trail — append-only, tenant RLS.

Revision ID: 085
Revises: 084
"""

from alembic import op

revision = "085"
down_revision = "084"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cdm_copilot_audit (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
          user_id TEXT,
          session_id UUID,
          query_id UUID NOT NULL,
          query_text TEXT NOT NULL,
          query_mode TEXT NOT NULL DEFAULT 'ask',
          query_context JSONB NOT NULL DEFAULT '{}'::jsonb,
          response_text TEXT,
          response_confidence DOUBLE PRECISION,
          response_sources JSONB NOT NULL DEFAULT '[]'::jsonb,
          llm_provider TEXT,
          llm_model TEXT,
          llm_tokens_input INT,
          llm_tokens_output INT,
          llm_latency_ms INT,
          downstream_action_id UUID,
          integrity_hash TEXT,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          created_at_epoch BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM now())::bigint),
          UNIQUE (tenant_id, query_id)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_cdm_copilot_audit_tenant ON cdm_copilot_audit (tenant_id, created_at DESC)")
    op.execute("ALTER TABLE cdm_copilot_audit ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE cdm_copilot_audit FORCE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_copilot_audit")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON cdm_copilot_audit
        FOR ALL
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION cdm_copilot_audit_append_only() RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'cdm_copilot_audit is append-only';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute("DROP TRIGGER IF EXISTS trg_copilot_audit_no_update ON cdm_copilot_audit")
    op.execute(
        """
        CREATE TRIGGER trg_copilot_audit_no_update
        BEFORE UPDATE OR DELETE ON cdm_copilot_audit
        FOR EACH ROW EXECUTE FUNCTION cdm_copilot_audit_append_only()
        """
    )
    op.execute("REVOKE UPDATE, DELETE ON cdm_copilot_audit FROM PUBLIC")


def downgrade():
    op.execute("DROP TABLE IF EXISTS cdm_copilot_audit CASCADE")
    op.execute("DROP FUNCTION IF EXISTS cdm_copilot_audit_append_only()")
