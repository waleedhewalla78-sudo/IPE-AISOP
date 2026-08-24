"""Data quality report store.

Revision ID: 086
Revises: 085
"""

from alembic import op

revision = "086"
down_revision = "085"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cdm_data_quality_report (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
          score NUMERIC NOT NULL,
          payload JSONB NOT NULL DEFAULT '{}'::jsonb,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_cdm_dq_report_tenant ON cdm_data_quality_report (tenant_id, created_at DESC)")
    op.execute("ALTER TABLE cdm_data_quality_report ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE cdm_data_quality_report FORCE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_data_quality_report")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON cdm_data_quality_report
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        """
    )


def downgrade():
    op.execute("DROP TABLE IF EXISTS cdm_data_quality_report CASCADE")
