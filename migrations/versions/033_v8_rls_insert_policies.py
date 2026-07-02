"""Fix RLS INSERT policies for v8 tenant-scoped tables.

Revision ID: 033
Revises: 032
"""
from alembic import op

revision = "033"
down_revision = "032"
branch_labels = None
depends_on = None

_TABLES = [
    "cdm_copilot_session",
    "cdm_demand_signal",
    "cdm_demand_forecast",
    "cdm_scenario_parameter",
    "cdm_scenario_result",
    "cdm_customer_order",
    "cdm_customer_order_line",
    "cdm_order_promise",
    "cdm_supply_plan",
    "cdm_equipment_asset",
    "cdm_engineering_material",
    "cdm_design_recommendation",
    "cdm_design_rule",
    "cdm_procurement_spend",
    "cdm_procurement_compliance_check",
]


def upgrade():
    for table in _TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
            WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
            """
        )


def downgrade():
    for table in _TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
            """
        )
