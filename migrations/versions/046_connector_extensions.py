"""Migration 046 — Connector extensions: lead time history + product cost/price fields."""

from alembic import op

revision = "046"
down_revision = "045"
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
        CREATE TABLE IF NOT EXISTS cdm_lead_time_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
            product_id UUID NOT NULL REFERENCES cdm_product(id) ON DELETE CASCADE,
            supplier_id UUID NULL REFERENCES cdm_supplier(id),
            po_erp_id VARCHAR(100),
            order_date DATE,
            expected_date DATE,
            actual_receipt_date DATE,
            lead_time_days INTEGER,
            lead_time_variance_days INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_lth_tenant_product "
        "ON cdm_lead_time_history (tenant_id, product_id)"
    )
    _rls("cdm_lead_time_history")

    op.execute("ALTER TABLE cdm_product ADD COLUMN IF NOT EXISTS unit_cost NUMERIC(18,4)")
    op.execute("ALTER TABLE cdm_product ADD COLUMN IF NOT EXISTS list_price NUMERIC(18,4)")
    op.execute("ALTER TABLE cdm_product ADD COLUMN IF NOT EXISTS weight NUMERIC(10,4)")
    op.execute("ALTER TABLE cdm_demand_line ADD COLUMN IF NOT EXISTS revenue NUMERIC(18,2)")


def downgrade():
    op.execute("ALTER TABLE cdm_demand_line DROP COLUMN IF EXISTS revenue")
    op.execute("ALTER TABLE cdm_product DROP COLUMN IF EXISTS weight")
    op.execute("ALTER TABLE cdm_product DROP COLUMN IF EXISTS list_price")
    op.execute("ALTER TABLE cdm_product DROP COLUMN IF EXISTS unit_cost")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_lead_time_history")
    op.execute("DROP TABLE IF EXISTS cdm_lead_time_history")
