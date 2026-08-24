"""Promote demo_* Excel staging to canonical ingest tables with RLS.

Revision ID: 083
Revises: 082

demo_* used TEXT PKs and skipped RLS (Spec 040 NFR-040-05). Operational CDM
tables are UUID/FK-incompatible. This creates cdm_ingest_* with tenant_id +
FORCE RLS, copies leftover demo_* rows into the Star Trans lab tenant, then
drops demo_*.
"""

from alembic import op

revision = "083"
down_revision = "082"
branch_labels = None
depends_on = None

STAR_TRANS_TENANT = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

# (canonical_table, demo_table, natural_key, extra_columns_sql)
INGEST = [
    ("cdm_ingest_plant", "demo_plants", "plant_id", "name TEXT"),
    ("cdm_ingest_product", "demo_products", "product_id", "name TEXT, product_type TEXT, uom TEXT"),
    ("cdm_ingest_material", "demo_materials", "material_id", "name TEXT"),
    ("cdm_ingest_work_center", "demo_work_centers", "work_center_id", "name TEXT, capacity_hours NUMERIC"),
    ("cdm_ingest_customer", "demo_customers", "customer_id", "name TEXT"),
    ("cdm_ingest_supplier", "demo_suppliers", "supplier_id", "name TEXT"),
    ("cdm_ingest_bom", "demo_boms", "bom_id", "product_id TEXT"),
    (
        "cdm_ingest_bom_component",
        "demo_bom_components",
        "bom_component_id",
        "bom_id TEXT, component_product_id TEXT, qty NUMERIC",
    ),
    ("cdm_ingest_routing", "demo_routings", "routing_id", "product_id TEXT"),
    (
        "cdm_ingest_routing_operation",
        "demo_routing_operations",
        "operation_id",
        "routing_id TEXT, work_center_id TEXT, duration_hours NUMERIC, sequence_no INT",
    ),
    (
        "cdm_ingest_manufacturing_order",
        "demo_manufacturing_orders",
        "mo_id",
        "product_id TEXT, qty NUMERIC, feasibility NUMERIC, status TEXT, due_date TEXT, planned_start TEXT",
    ),
    ("cdm_ingest_sales_order", "demo_sales_orders", "so_id", "customer_id TEXT"),
    ("cdm_ingest_purchase_order", "demo_purchase_orders", "po_id", "supplier_id TEXT"),
    ("cdm_ingest_inventory", "demo_inventory", "inventory_id", "product_id TEXT, qty NUMERIC"),
    ("cdm_ingest_capacity_calendar", "demo_capacity_calendar", "calendar_id", "work_center_id TEXT"),
    ("cdm_ingest_lead_time", "demo_lead_times", "lead_time_id", ""),
    ("cdm_ingest_cost_data", "demo_cost_data", "cost_id", ""),
    ("cdm_ingest_demand_forecast", "demo_demand_forecast", "forecast_id", ""),
    ("cdm_ingest_demand_history", "demo_demand_history", "history_id", ""),
    ("cdm_ingest_quality_result", "demo_quality_results", "quality_id", ""),
]


def _rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
    op.execute(
        f"""
        CREATE POLICY tenant_isolation ON {table}
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        """
    )


def upgrade():
    for table, _demo, nk, extra in INGEST:
        extra_sql = f", {extra}" if extra.strip() else ""
        op.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table} (
              id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
              tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
              {nk} TEXT NOT NULL
              {extra_sql},
              payload JSONB NOT NULL DEFAULT '{{}}'::jsonb,
              created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
              updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
              UNIQUE (tenant_id, {nk})
            )
            """
        )
        op.execute(f"CREATE INDEX IF NOT EXISTS ix_{table}_tenant ON {table} (tenant_id)")
        _rls(table)

    for table, demo, nk, extra in INGEST:
        extra_names = [c.strip().split()[0] for c in extra.split(",") if c.strip()]
        extra_src = (", " + ", ".join(extra_names)) if extra_names else ""
        dest_cols = ", ".join(["tenant_id", nk, *extra_names, "payload"])
        op.execute(
            f"""
            DO $$
            BEGIN
              IF to_regclass('public.{demo}') IS NOT NULL THEN
                INSERT INTO {table} ({dest_cols})
                SELECT '{STAR_TRANS_TENANT}'::uuid, {nk}{extra_src}, COALESCE(payload, '{{}}'::jsonb)
                FROM {demo}
                ON CONFLICT (tenant_id, {nk}) DO NOTHING;
              END IF;
            END $$;
            """
        )

    for _c, demo, _n, _e in reversed(INGEST):
        op.execute(f"DROP TABLE IF EXISTS {demo} CASCADE")


def downgrade():
    for table, _demo, _nk, _extra in reversed(INGEST):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
