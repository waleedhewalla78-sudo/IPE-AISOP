"""Spec 029 — enable RLS on remaining CDM gap tables (TC-RLS-03).

Revision ID: 068
Revises: 067
"""

from alembic import op

revision = "068"
down_revision = "067"
branch_labels = None
depends_on = None


def _enable_tenant_policy(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
    op.execute(
        f"""
        CREATE POLICY tenant_isolation ON {table}
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        """
    )


def _enable_parent_join_policy(table: str, parent_sql: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
    op.execute(
        f"""
        CREATE POLICY tenant_isolation ON {table}
        USING ({parent_sql})
        WITH CHECK ({parent_sql})
        """
    )


def upgrade():
    # Tenant-scoped tables that had POLICY without ENABLE (or never enabled)
    for t in (
        "cdm_location",
        "cdm_project_plan",
        "cdm_project_plan_version",
        "cdm_sop_forecast",
        "cdm_sop_plan",
    ):
        _enable_tenant_policy(t)

    # Parent-joined children (no direct tenant_id)
    _enable_parent_join_policy(
        "cdm_scenario_demand",
        "EXISTS (SELECT 1 FROM cdm_scenario s WHERE s.id = scenario_id "
        "AND s.tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)",
    )
    _enable_parent_join_policy(
        "cdm_scenario_supply",
        "EXISTS (SELECT 1 FROM cdm_scenario s WHERE s.id = scenario_id "
        "AND s.tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)",
    )
    _enable_parent_join_policy(
        "cdm_scenario_resource",
        "EXISTS (SELECT 1 FROM cdm_scenario s WHERE s.id = scenario_id "
        "AND s.tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)",
    )
    _enable_parent_join_policy(
        "cdm_worker_skill_link",
        "EXISTS (SELECT 1 FROM cdm_worker w WHERE w.id = worker_id "
        "AND w.tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)",
    )

    # Tenant registry: self-scope only
    op.execute("ALTER TABLE cdm_tenant ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_self ON cdm_tenant")
    op.execute(
        """
        CREATE POLICY tenant_self ON cdm_tenant
        USING (id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        """
    )


def downgrade():
    for t in (
        "cdm_location",
        "cdm_project_plan",
        "cdm_project_plan_version",
        "cdm_sop_forecast",
        "cdm_sop_plan",
        "cdm_scenario_demand",
        "cdm_scenario_supply",
        "cdm_scenario_resource",
        "cdm_worker_skill_link",
    ):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {t}")
        op.execute(f"ALTER TABLE {t} DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_self ON cdm_tenant")
    op.execute("ALTER TABLE cdm_tenant DISABLE ROW LEVEL SECURITY")
