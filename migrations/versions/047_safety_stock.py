"""Migration 047 — Statistical safety stock results table."""

from alembic import op

revision = "047"
down_revision = "046"
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
        CREATE TABLE IF NOT EXISTS cdm_safety_stock (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
            product_id UUID NOT NULL REFERENCES cdm_product(id) ON DELETE CASCADE,
            location_id UUID NULL REFERENCES cdm_plant(id),
            calculation_date DATE NOT NULL,
            service_level_target_pct NUMERIC(5,2),
            z_score NUMERIC(6,4),
            avg_demand_per_period NUMERIC(18,4),
            demand_stddev NUMERIC(18,4),
            demand_cv NUMERIC(8,4),
            avg_lead_time_periods NUMERIC(10,2),
            lead_time_stddev NUMERIC(10,2),
            lead_time_cv NUMERIC(8,4),
            safety_stock_qty NUMERIC(18,4),
            safety_stock_demand_component NUMERIC(18,4),
            safety_stock_leadtime_component NUMERIC(18,4),
            reorder_point_qty NUMERIC(18,4),
            current_stock_qty NUMERIC(18,4) NULL,
            delta_qty NUMERIC(18,4) NULL,
            delta_pct NUMERIC(10,4) NULL,
            prior_safety_stock_qty NUMERIC(18,4) NULL,
            cycle_change_qty NUMERIC(18,4) NULL,
            unit_cost NUMERIC(18,4) NULL,
            safety_stock_value NUMERIC(18,2) NULL,
            delta_value NUMERIC(18,2) NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_ss_tenant_product
        ON cdm_safety_stock (tenant_id, product_id, calculation_date)
        """
    )
    _rls("cdm_safety_stock")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_safety_stock")
    op.execute("DROP TABLE IF EXISTS cdm_safety_stock")
