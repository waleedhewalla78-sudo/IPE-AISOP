"""Migration 042 — Sprint S11 S&OP synthesis report storage."""

from alembic import op

revision = "042"
down_revision = "041"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS cdm_sop_report (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
            report_name VARCHAR(256) NOT NULL,
            horizon_weeks INTEGER NOT NULL DEFAULT 12,
            status VARCHAR(20) NOT NULL DEFAULT 'draft',
            summary JSONB NOT NULL DEFAULT '{}',
            gap_analysis JSONB NOT NULL DEFAULT '{}',
            recommendations JSONB NOT NULL DEFAULT '[]',
            generated_by VARCHAR(128),
            generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_sop_report_tenant_generated
        ON cdm_sop_report (tenant_id, generated_at DESC)
    """)
    op.execute("ALTER TABLE cdm_sop_report ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_sop_report")
    op.execute("""
        CREATE POLICY tenant_isolation ON cdm_sop_report
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    """)


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_sop_report")
    op.execute("DROP TABLE IF EXISTS cdm_sop_report")
