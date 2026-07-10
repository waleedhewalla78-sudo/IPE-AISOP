"""Migration 045 — Forecast quality snapshots, errors, stability."""

from alembic import op

revision = "045"
down_revision = "044"
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
        CREATE TABLE IF NOT EXISTS cdm_forecast_snapshot (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
            product_id UUID NOT NULL REFERENCES cdm_product(id) ON DELETE CASCADE,
            location_id UUID NULL REFERENCES cdm_plant(id),
            snapshot_date DATE NOT NULL,
            target_period_start DATE NOT NULL,
            target_period_type VARCHAR(10) NOT NULL DEFAULT 'month',
            forecast_qty NUMERIC(18,4) NOT NULL,
            forecast_source VARCHAR(50) NOT NULL,
            model_id VARCHAR(100) NULL,
            model_version VARCHAR(50) NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_fsnap_tenant_product "
        "ON cdm_forecast_snapshot (tenant_id, product_id, snapshot_date)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_fsnap_target "
        "ON cdm_forecast_snapshot (tenant_id, target_period_start)"
    )
    _rls("cdm_forecast_snapshot")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cdm_forecast_error (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
            product_id UUID NOT NULL REFERENCES cdm_product(id) ON DELETE CASCADE,
            location_id UUID NULL,
            period_start DATE NOT NULL,
            period_type VARCHAR(10) NOT NULL DEFAULT 'month',
            lag_periods INTEGER NOT NULL,
            forecast_source VARCHAR(50) NOT NULL,
            forecast_qty NUMERIC(18,4),
            actuals_qty NUMERIC(18,4),
            absolute_error NUMERIC(18,4),
            error_pct NUMERIC(10,4),
            bias NUMERIC(18,4),
            bias_pct NUMERIC(10,4),
            mase_component NUMERIC(10,4),
            calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ferr_tenant_product "
        "ON cdm_forecast_error (tenant_id, product_id, period_start, lag_periods)"
    )
    _rls("cdm_forecast_error")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cdm_forecast_stability (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
            product_id UUID NOT NULL REFERENCES cdm_product(id) ON DELETE CASCADE,
            target_period_start DATE NOT NULL,
            cycle_date DATE NOT NULL,
            prior_cycle_date DATE NULL,
            current_forecast_qty NUMERIC(18,4),
            prior_forecast_qty NUMERIC(18,4) NULL,
            change_qty NUMERIC(18,4) NULL,
            change_pct NUMERIC(10,4) NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    _rls("cdm_forecast_stability")


def downgrade():
    for table in ("cdm_forecast_stability", "cdm_forecast_error", "cdm_forecast_snapshot"):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"DROP TABLE IF EXISTS {table}")
