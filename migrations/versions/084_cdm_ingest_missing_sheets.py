"""Add cdm_ingest tables for remaining Star Trans workbook sheets.

Revision ID: 084
Revises: 083

083 covered demo_* promotion (20 tables). The Star Trans template has 23 data
sheets; header/line and calendar/employee/event sheets were unmapped.
"""

from alembic import op

revision = "084"
down_revision = "083"
branch_labels = None
depends_on = None

# (table, natural_key, extra_columns_sql)
INGEST = [
    (
        "cdm_ingest_calendar_shift",
        "shift_id",
        "calendar_id TEXT, day_of_week TEXT, shift_number TEXT, "
        "shift_start_time TEXT, shift_end_time TEXT, "
        "break_duration_minutes NUMERIC, is_working TEXT",
    ),
    (
        "cdm_ingest_calendar_exception",
        "exception_id",
        "calendar_id TEXT, exception_date_start TEXT, exception_date_end TEXT, "
        "exception_type TEXT, capacity_override_pct NUMERIC, description TEXT",
    ),
    (
        "cdm_ingest_employee",
        "employee_id",
        "employee_code TEXT, plant_id TEXT, department TEXT, role TEXT, "
        "employee_name TEXT, status TEXT, cost_per_hour NUMERIC",
    ),
    (
        "cdm_ingest_employee_skill",
        "employee_skill_id",
        "employee_id TEXT, skill_code TEXT, skill_name TEXT, skill_level TEXT, "
        "certified TEXT, certification_expiry TEXT",
    ),
    (
        "cdm_ingest_sales_order_line",
        "so_line_id",
        "sales_order_id TEXT, line_number TEXT, product_id TEXT, qty NUMERIC, status TEXT",
    ),
    (
        "cdm_ingest_purchase_order_line",
        "po_line_id",
        "purchase_order_id TEXT, line_number TEXT, material_id TEXT, qty NUMERIC, status TEXT",
    ),
    (
        "cdm_ingest_execution_event",
        "event_id",
        "event_type TEXT, event_datetime TEXT, mo_id TEXT, operation_id TEXT, "
        "work_center_id TEXT, employee_id TEXT, quantity NUMERIC",
    ),
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
    for table, nk, extra in INGEST:
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


def downgrade():
    for table, _nk, _extra in reversed(INGEST):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
