"""Demo CDM ingest for Star Trans workbook (simplified — no RLS/GIN)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.startrans_workbook import NATURAL_KEYS, WorkbookParseResult

# Sheet → demo staging table
SHEET_TABLE: dict[str, str] = {
    "01_Products": "demo_products",
    "02_WorkCenters": "demo_work_centers",
    "03_BOM": "demo_boms",
    "04_Routing": "demo_routings",
    "05_Customers": "demo_customers",
    "06_Suppliers": "demo_suppliers",
    "07_ManufacturingOrders": "demo_manufacturing_orders",
    "08_SalesOrders": "demo_sales_orders",
    "09_PurchaseOrders": "demo_purchase_orders",
    "10_Inventory": "demo_inventory",
    "11_CapacityCalendar": "demo_capacity_calendar",
    "12_LeadTimes": "demo_lead_times",
    "13_CostData": "demo_cost_data",
    "14_DemandForecast": "demo_demand_forecast",
    "15_DemandHistory": "demo_demand_history",
    "16_QualityResults": "demo_quality_results",
}

# FK checks: sheet → [(field, ref_table, ref_key)]
FK_RULES: dict[str, list[tuple[str, str, str]]] = {
    "07_ManufacturingOrders": [
        ("product_id", "demo_products", "product_id"),
        ("product_code", "demo_products", "product_id"),
    ],
    "03_BOM": [("product_id", "demo_products", "product_id")],
    "04_Routing": [("product_id", "demo_products", "product_id")],
    "10_Inventory": [("product_id", "demo_products", "product_id")],
    "08_SalesOrders": [("customer_id", "demo_customers", "customer_id")],
    "09_PurchaseOrders": [("supplier_id", "demo_suppliers", "supplier_id")],
    "22_BOMComponents": [("bom_id", "demo_boms", "bom_id")],
    "23_RoutingOperations": [
        ("routing_id", "demo_routings", "routing_id"),
        ("work_center_id", "demo_work_centers", "work_center_id"),
    ],
}


async def ensure_demo_tables(session: AsyncSession) -> None:
    """Create simplified demo entity tables if missing."""
    ddl = """
    CREATE TABLE IF NOT EXISTS demo_products (
      product_id TEXT PRIMARY KEY, name TEXT, product_type TEXT, uom TEXT, payload JSONB DEFAULT '{}'
    );
    CREATE TABLE IF NOT EXISTS demo_work_centers (
      work_center_id TEXT PRIMARY KEY, name TEXT, capacity_hours NUMERIC, payload JSONB DEFAULT '{}'
    );
    CREATE TABLE IF NOT EXISTS demo_customers (
      customer_id TEXT PRIMARY KEY, name TEXT, payload JSONB DEFAULT '{}'
    );
    CREATE TABLE IF NOT EXISTS demo_suppliers (
      supplier_id TEXT PRIMARY KEY, name TEXT, payload JSONB DEFAULT '{}'
    );
    CREATE TABLE IF NOT EXISTS demo_boms (
      bom_id TEXT PRIMARY KEY, product_id TEXT, payload JSONB DEFAULT '{}'
    );
    CREATE TABLE IF NOT EXISTS demo_routings (
      routing_id TEXT PRIMARY KEY, product_id TEXT, payload JSONB DEFAULT '{}'
    );
    CREATE TABLE IF NOT EXISTS demo_manufacturing_orders (
      mo_id TEXT PRIMARY KEY, product_id TEXT, qty NUMERIC, feasibility NUMERIC,
      status TEXT, due_date TEXT, payload JSONB DEFAULT '{}'
    );
    CREATE TABLE IF NOT EXISTS demo_sales_orders (
      so_id TEXT PRIMARY KEY, customer_id TEXT, payload JSONB DEFAULT '{}'
    );
    CREATE TABLE IF NOT EXISTS demo_purchase_orders (
      po_id TEXT PRIMARY KEY, supplier_id TEXT, payload JSONB DEFAULT '{}'
    );
    CREATE TABLE IF NOT EXISTS demo_inventory (
      inventory_id TEXT PRIMARY KEY, product_id TEXT, qty NUMERIC, payload JSONB DEFAULT '{}'
    );
    CREATE TABLE IF NOT EXISTS demo_capacity_calendar (
      calendar_id TEXT PRIMARY KEY, work_center_id TEXT, payload JSONB DEFAULT '{}'
    );
    CREATE TABLE IF NOT EXISTS demo_lead_times (
      lead_time_id TEXT PRIMARY KEY, payload JSONB DEFAULT '{}'
    );
    CREATE TABLE IF NOT EXISTS demo_cost_data (
      cost_id TEXT PRIMARY KEY, payload JSONB DEFAULT '{}'
    );
    CREATE TABLE IF NOT EXISTS demo_demand_forecast (
      forecast_id TEXT PRIMARY KEY, payload JSONB DEFAULT '{}'
    );
    CREATE TABLE IF NOT EXISTS demo_demand_history (
      history_id TEXT PRIMARY KEY, payload JSONB DEFAULT '{}'
    );
    CREATE TABLE IF NOT EXISTS demo_quality_results (
      quality_id TEXT PRIMARY KEY, payload JSONB DEFAULT '{}'
    );
    CREATE INDEX IF NOT EXISTS idx_demo_mo_feasibility ON demo_manufacturing_orders (feasibility);
    CREATE INDEX IF NOT EXISTS idx_demo_mo_product ON demo.manufacturing_orders (product_id);
    """
    # Fix typo in index — use correct table name
    ddl = ddl.replace(
        "CREATE INDEX IF NOT EXISTS idx_demo_mo_product ON demo.manufacturing_orders (product_id);",
        "CREATE INDEX IF NOT EXISTS idx_demo_mo_product ON demo_manufacturing_orders (product_id);",
    )
    for stmt in ddl.split(";"):
        s = stmt.strip()
        if s:
            await session.execute(text(s))
    await session.commit()


async def _existing_keys(session: AsyncSession, table: str, key: str) -> set[str]:
    try:
        result = await session.execute(text(f"SELECT {key} FROM {table}"))  # noqa: S608
        return {str(r[0]) for r in result.fetchall() if r[0] is not None}
    except Exception:
        await session.rollback()
        return set()


async def ingest_workbook(
    session: AsyncSession,
    parsed: WorkbookParseResult,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Validate FKs and upsert by natural key. Collect all errors (batch report)."""
    await ensure_demo_tables(session)

    # Seed key caches from already-parsed sheets (in-workbook refs) + DB
    key_cache: dict[str, set[str]] = {}
    for sheet, table in SHEET_TABLE.items():
        nk = NATURAL_KEYS.get(sheet, "")
        if not nk:
            continue
        db_keys = await _existing_keys(session, table, nk)
        sheet_res = parsed.sheet_results.get(sheet)
        if sheet_res and not sheet_res.skipped:
            for row in sheet_res.rows:
                val = row.get(nk) or row.get("product_code") or row.get("work_center_code")
                if val is not None:
                    db_keys.add(str(val))
        key_cache[table] = db_keys

    batch_errors: list[dict[str, Any]] = []
    upserted = 0
    rejected = 0
    per_sheet: list[dict[str, Any]] = []

    # Masters first, then dependents
    order = list(SHEET_TABLE.keys())
    for sheet in order:
        table = SHEET_TABLE[sheet]
        nk = NATURAL_KEYS[sheet]
        res = parsed.sheet_results.get(sheet)
        if not res or res.skipped:
            per_sheet.append({"sheet": sheet, "upserted": 0, "rejected": 0, "skipped": True})
            continue

        sheet_ok = 0
        sheet_fail = 0
        for i, row in enumerate(res.rows):
            row_err = _check_fks(sheet, row, key_cache)
            if row_err:
                batch_errors.append(
                    {"sheet": sheet, "row": i + 6, "message": row_err, "severity": "error"}
                )
                sheet_fail += 1
                rejected += 1
                continue

            key_val = row.get(nk) or row.get("product_code") or row.get("work_center_code")
            if key_val is None:
                batch_errors.append(
                    {
                        "sheet": sheet,
                        "row": i + 6,
                        "message": f"Missing natural key {nk}",
                        "severity": "error",
                    }
                )
                sheet_fail += 1
                rejected += 1
                continue

            if dry_run:
                sheet_ok += 1
                upserted += 1
                key_cache.setdefault(table, set()).add(str(key_val))
                continue

            try:
                await _upsert_row(session, table, nk, str(key_val), row)
                sheet_ok += 1
                upserted += 1
                key_cache.setdefault(table, set()).add(str(key_val))
            except Exception as exc:  # noqa: BLE001
                batch_errors.append(
                    {
                        "sheet": sheet,
                        "row": i + 6,
                        "message": str(exc),
                        "severity": "error",
                    }
                )
                sheet_fail += 1
                rejected += 1
                await session.rollback()
                await ensure_demo_tables(session)

        per_sheet.append(
            {"sheet": sheet, "upserted": sheet_ok, "rejected": sheet_fail, "skipped": False}
        )

    if not dry_run:
        try:
            await session.commit()
        except Exception:
            await session.rollback()

    return {
        "upload_id": str(uuid4()),
        "dry_run": dry_run,
        "upserted": upserted,
        "rejected": rejected,
        "errors": batch_errors,
        "sheets": per_sheet,
    }


def _check_fks(sheet: str, row: dict[str, Any], key_cache: dict[str, set[str]]) -> str | None:
    for field, ref_table, ref_key in FK_RULES.get(sheet, []):
        val = row.get(field)
        if val is None or str(val).strip() == "":
            continue
        known = key_cache.get(ref_table, set())
        # If ref table empty (masters not loaded yet), skip hard fail for demo soft mode
        if not known:
            continue
        if str(val) not in known:
            return f"FK {field}={val} not found in {ref_table}.{ref_key}"
    return None


async def _upsert_row(
    session: AsyncSession,
    table: str,
    nk: str,
    key_val: str,
    row: dict[str, Any],
) -> None:
    import json

    payload = json.dumps({k: v for k, v in row.items() if v is not None}, default=str)
    # Column mapping per table
    if table == "demo_products":
        await session.execute(
            text(
                """
                INSERT INTO demo_products (product_id, name, product_type, uom, payload)
                VALUES (:id, :name, :ptype, :uom, CAST(:payload AS jsonb))
                ON CONFLICT (product_id) DO UPDATE SET
                  name = EXCLUDED.name, product_type = EXCLUDED.product_type,
                  uom = EXCLUDED.uom, payload = EXCLUDED.payload
                """
            ),
            {
                "id": key_val,
                "name": row.get("name") or row.get("product_name") or key_val,
                "ptype": row.get("product_type") or row.get("type"),
                "uom": row.get("uom") or "EA",
                "payload": payload,
            },
        )
    elif table == "demo_work_centers":
        await session.execute(
            text(
                """
                INSERT INTO demo_work_centers (work_center_id, name, capacity_hours, payload)
                VALUES (:id, :name, :cap, CAST(:payload AS jsonb))
                ON CONFLICT (work_center_id) DO UPDATE SET
                  name = EXCLUDED.name, capacity_hours = EXCLUDED.capacity_hours,
                  payload = EXCLUDED.payload
                """
            ),
            {
                "id": key_val,
                "name": row.get("name") or key_val,
                "cap": row.get("capacity_hours") or row.get("capacity"),
                "payload": payload,
            },
        )
    elif table == "demo_manufacturing_orders":
        await session.execute(
            text(
                """
                INSERT INTO demo_manufacturing_orders
                  (mo_id, product_id, qty, feasibility, status, due_date, payload)
                VALUES (:id, :pid, :qty, :feas, :status, :due, CAST(:payload AS jsonb))
                ON CONFLICT (mo_id) DO UPDATE SET
                  product_id = EXCLUDED.product_id, qty = EXCLUDED.qty,
                  feasibility = EXCLUDED.feasibility, status = EXCLUDED.status,
                  due_date = EXCLUDED.due_date, payload = EXCLUDED.payload
                """
            ),
            {
                "id": key_val,
                "pid": row.get("product_id") or row.get("product_code"),
                "qty": row.get("qty") or row.get("quantity"),
                "feas": row.get("feasibility") or row.get("feasibility_score"),
                "status": row.get("status") or "planned",
                "due": row.get("due_date") or row.get("required_date"),
                "payload": payload,
            },
        )
    elif table in (
        "demo_customers",
        "demo_suppliers",
        "demo_boms",
        "demo_routings",
        "demo_sales_orders",
        "demo_purchase_orders",
        "demo_inventory",
        "demo_capacity_calendar",
        "demo_lead_times",
        "demo_cost_data",
        "demo_demand_forecast",
        "demo_demand_history",
        "demo_quality_results",
    ):
        # Generic: natural key + optional FK cols + payload
        cols = {nk: key_val}
        for opt in ("product_id", "customer_id", "supplier_id", "work_center_id", "qty", "name"):
            if opt in row and opt != nk:
                cols[opt] = row[opt]
        col_names = list(cols.keys()) + ["payload"]
        placeholders = [f":{c}" for c in cols] + ["CAST(:payload AS jsonb)"]
        updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c != nk)
        updates = (updates + ", " if updates else "") + "payload = EXCLUDED.payload"
        sql = (
            f"INSERT INTO {table} ({', '.join(col_names)}) "
            f"VALUES ({', '.join(placeholders)}) "
            f"ON CONFLICT ({nk}) DO UPDATE SET {updates}"
        )
        params = {**cols, "payload": payload}
        await session.execute(text(sql), params)  # noqa: S608
    else:
        raise ValueError(f"Unsupported table {table}")
