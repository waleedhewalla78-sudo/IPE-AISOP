"""Migration 039 — OTD snapshot table for trend tracking (W1-07 / Sprint S6)."""

from alembic import op

revision = "039"
down_revision = "043"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS cdm_otd_snapshot (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id),
            snapshot_date DATE NOT NULL,
            period VARCHAR(16) NOT NULL,
            supplier_id UUID REFERENCES cdm_supplier(id),
            work_center_id UUID REFERENCES cdm_work_center(id),
            plant_id UUID REFERENCES cdm_plant(id),
            otd_pct NUMERIC(5, 1),
            completed_mos INTEGER NOT NULL DEFAULT 0,
            on_time_mos INTEGER NOT NULL DEFAULT 0,
            orders_at_risk INTEGER NOT NULL DEFAULT 0,
            avg_delay_days NUMERIC(8, 2),
            chaos_cost_usd NUMERIC(14, 2) NOT NULL DEFAULT 0,
            metadata JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_otd_snapshot_dims
        ON cdm_otd_snapshot (
            tenant_id,
            snapshot_date,
            period,
            COALESCE(supplier_id, '00000000-0000-0000-0000-000000000000'::uuid),
            COALESCE(work_center_id, '00000000-0000-0000-0000-000000000000'::uuid),
            COALESCE(plant_id, '00000000-0000-0000-0000-000000000000'::uuid)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_otd_snapshot_tenant_date
        ON cdm_otd_snapshot (tenant_id, snapshot_date DESC)
    """)
    op.execute("ALTER TABLE cdm_otd_snapshot ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_otd_snapshot")
    op.execute("""
        CREATE POLICY tenant_isolation ON cdm_otd_snapshot
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    """)


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_otd_snapshot")
    op.execute("DROP TABLE IF EXISTS cdm_otd_snapshot")
