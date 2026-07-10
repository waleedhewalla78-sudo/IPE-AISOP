"""Migration 048 — Capacity utilisation alerts."""

from alembic import op

revision = "048"
down_revision = "047"
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
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cdm_capacity_utilisation (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
            work_center_id UUID NOT NULL REFERENCES cdm_work_center(id) ON DELETE CASCADE,
            period_start DATE NOT NULL,
            period_type VARCHAR(10) NOT NULL DEFAULT 'week',
            capacity_available_hours NUMERIC(10,2),
            capacity_used_hours NUMERIC(10,2),
            utilisation_pct NUMERIC(6,2),
            overload BOOLEAN NOT NULL DEFAULT FALSE,
            overload_hours NUMERIC(10,2) NOT NULL DEFAULT 0,
            calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_cutil_tenant_wc "
        "ON cdm_capacity_utilisation (tenant_id, work_center_id, period_start)"
    )
    _rls("cdm_capacity_utilisation")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cdm_capacity_alert_config (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
            overload_threshold_pct NUMERIC(5,2) NOT NULL DEFAULT 90.0,
            critical_threshold_pct NUMERIC(5,2) NOT NULL DEFAULT 100.0,
            alert_enabled BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_capacity_alert_config_tenant UNIQUE (tenant_id)
        )
        """
    )
    _rls("cdm_capacity_alert_config")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_capacity_alert_config")
    op.execute("DROP TABLE IF EXISTS cdm_capacity_alert_config")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_capacity_utilisation")
    op.execute("DROP TABLE IF EXISTS cdm_capacity_utilisation")
