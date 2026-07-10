"""Migration 049 — S&OP process engine tables."""

from alembic import op

revision = "049"
down_revision = "048"
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
        CREATE TABLE IF NOT EXISTS cdm_sop_cycle (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
            cycle_name VARCHAR(100),
            cycle_month DATE NOT NULL,
            status VARCHAR(30) NOT NULL DEFAULT 'draft'
                CHECK (status IN (
                    'draft','demand_review','supply_review',
                    'reconciliation','management_review','closed'
                )),
            demand_review_deadline TIMESTAMPTZ NULL,
            supply_review_deadline TIMESTAMPTZ NULL,
            reconciliation_deadline TIMESTAMPTZ NULL,
            management_review_deadline TIMESTAMPTZ NULL,
            created_by UUID NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            closed_at TIMESTAMPTZ NULL
        )
        """
    )
    _rls("cdm_sop_cycle")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cdm_sop_version (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
            cycle_id UUID NOT NULL REFERENCES cdm_sop_cycle(id) ON DELETE CASCADE,
            version_type VARCHAR(20) NOT NULL
                CHECK (version_type IN ('baseline','upside','downside','whatif')),
            version_name VARCHAR(100),
            description TEXT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_by UUID NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    _rls("cdm_sop_version")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cdm_consensus_demand (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
            version_id UUID NOT NULL REFERENCES cdm_sop_version(id) ON DELETE CASCADE,
            product_id UUID NOT NULL REFERENCES cdm_product(id) ON DELETE CASCADE,
            location_id UUID NULL,
            customer_id UUID NULL,
            period_start DATE NOT NULL,
            period_type VARCHAR(10) NOT NULL DEFAULT 'month',
            sales_forecast_qty NUMERIC(18,4) NULL,
            marketing_forecast_qty NUMERIC(18,4) NULL,
            statistical_forecast_qty NUMERIC(18,4) NULL,
            finance_plan_qty NUMERIC(18,4) NULL,
            consensus_qty NUMERIC(18,4),
            planned_price NUMERIC(18,4) NULL,
            consensus_revenue NUMERIC(18,2) NULL,
            cost_per_unit NUMERIC(18,4) NULL,
            consensus_cost NUMERIC(18,2) NULL,
            consensus_profit NUMERIC(18,2) NULL,
            constrained_demand_qty NUMERIC(18,4) NULL,
            constrained_revenue NUMERIC(18,2) NULL,
            lost_sales_qty NUMERIC(18,4) NULL,
            lost_sales_value NUMERIC(18,2) NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_cd_version_product
        ON cdm_consensus_demand (version_id, product_id, period_start)
        """
    )
    _rls("cdm_consensus_demand")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cdm_sop_stage_gate (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
            cycle_id UUID NOT NULL REFERENCES cdm_sop_cycle(id) ON DELETE CASCADE,
            stage VARCHAR(30) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending','approved','rejected')),
            approved_by UUID NULL,
            approved_at TIMESTAMPTZ NULL,
            notes TEXT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    _rls("cdm_sop_stage_gate")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cdm_sop_consensus_weight (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
            weight_sales NUMERIC(5,2) NOT NULL DEFAULT 0.30,
            weight_statistical NUMERIC(5,2) NOT NULL DEFAULT 0.40,
            weight_marketing NUMERIC(5,2) NOT NULL DEFAULT 0.20,
            weight_finance NUMERIC(5,2) NOT NULL DEFAULT 0.10,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_sop_consensus_weight_tenant UNIQUE (tenant_id)
        )
        """
    )
    _rls("cdm_sop_consensus_weight")


def downgrade():
    for table in (
        "cdm_sop_consensus_weight",
        "cdm_sop_stage_gate",
        "cdm_consensus_demand",
        "cdm_sop_version",
        "cdm_sop_cycle",
    ):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"DROP TABLE IF EXISTS {table}")
