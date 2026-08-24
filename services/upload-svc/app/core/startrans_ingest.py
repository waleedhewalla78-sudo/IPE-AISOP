"""Star Trans workbook ingest into RLS-scoped canonical ingest tables (BATCH1-1).

Maps each sheet to cdm_ingest_* rows, validates FK references, collects all
errors as a batch report, and upserts by (tenant_id, natural key).
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.startrans_workbook import NATURAL_KEYS, WorkbookParseResult, compose_natural_key

DEFAULT_TENANT_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

# Sheet → canonical ingest table (IPE_Data_Template_StarTrans_v1.xlsx; README excluded)
SHEET_TABLE: dict[str, str] = {
    "01_Plants": "cdm_ingest_plant",
    "08_Suppliers": "cdm_ingest_supplier",
    "09_Customers": "cdm_ingest_customer",
    "03a_Calendars": "cdm_ingest_capacity_calendar",
    "03b_CalendarShifts": "cdm_ingest_calendar_shift",
    "03c_CalendarExceptions": "cdm_ingest_calendar_exception",
    "02_WorkCenters": "cdm_ingest_work_center",
    "04_Products": "cdm_ingest_product",
    "05_Materials": "cdm_ingest_material",
    "06a_BOMHeaders": "cdm_ingest_bom",
    "07a_RoutingHeaders": "cdm_ingest_routing",
    "10a_Employees": "cdm_ingest_employee",
    "06b_BOMLines": "cdm_ingest_bom_component",
    "07b_RoutingOperations": "cdm_ingest_routing_operation",
    "10b_EmployeeSkills": "cdm_ingest_employee_skill",
    "11a_SalesOrderHeaders": "cdm_ingest_sales_order",
    "13a_PurchaseOrderHeaders": "cdm_ingest_purchase_order",
    "11b_SalesOrderLines": "cdm_ingest_sales_order_line",
    "13b_PurchaseOrderLines": "cdm_ingest_purchase_order_line",
    "12_ManufacturingOrders": "cdm_ingest_manufacturing_order",
    "14_Inventory": "cdm_ingest_inventory",
    "15_Forecasts": "cdm_ingest_demand_forecast",
    "16_ExecutionEvents": "cdm_ingest_execution_event",
}

# Table unique column (ON CONFLICT target) when it differs from Excel NATURAL_KEYS
TABLE_UNIQUE: dict[str, str] = {
    "cdm_ingest_sales_order": "so_id",
    "cdm_ingest_purchase_order": "po_id",
    "cdm_ingest_inventory": "inventory_id",
    "cdm_ingest_routing_operation": "operation_id",
}

# FK checks: sheet → [(field, ref_table, ref_key)]
FK_RULES: dict[str, list[tuple[str, str, str]]] = {
    "02_WorkCenters": [("plant_id", "cdm_ingest_plant", "plant_id")],
    "03b_CalendarShifts": [("calendar_id", "cdm_ingest_capacity_calendar", "calendar_id")],
    "03c_CalendarExceptions": [("calendar_id", "cdm_ingest_capacity_calendar", "calendar_id")],
    "04_Products": [("plant_id_primary", "cdm_ingest_plant", "plant_id")],
    "06a_BOMHeaders": [("product_id", "cdm_ingest_product", "product_id")],
    "06b_BOMLines": [("bom_id", "cdm_ingest_bom", "bom_id")],
    "07a_RoutingHeaders": [("product_id", "cdm_ingest_product", "product_id")],
    "07b_RoutingOperations": [
        ("routing_id", "cdm_ingest_routing", "routing_id"),
        ("work_center_id_primary", "cdm_ingest_work_center", "work_center_id"),
    ],
    "10a_Employees": [("plant_id", "cdm_ingest_plant", "plant_id")],
    "10b_EmployeeSkills": [("employee_id", "cdm_ingest_employee", "employee_id")],
    "11a_SalesOrderHeaders": [("customer_id", "cdm_ingest_customer", "customer_id")],
    "11b_SalesOrderLines": [
        ("sales_order_id", "cdm_ingest_sales_order", "so_id"),
        ("product_id", "cdm_ingest_product", "product_id"),
    ],
    "12_ManufacturingOrders": [
        ("product_id", "cdm_ingest_product", "product_id"),
        ("plant_id", "cdm_ingest_plant", "plant_id"),
    ],
    "13a_PurchaseOrderHeaders": [("supplier_id", "cdm_ingest_supplier", "supplier_id")],
    "13b_PurchaseOrderLines": [
        ("purchase_order_id", "cdm_ingest_purchase_order", "po_id"),
        ("material_id", "cdm_ingest_material", "material_id"),
    ],
    "16_ExecutionEvents": [("mo_id", "cdm_ingest_manufacturing_order", "mo_id")],
}


def _unique_col(sheet: str, table: str) -> str:
    return TABLE_UNIQUE.get(table, NATURAL_KEYS[sheet])


def _key_val(sheet: str, row: dict[str, Any], nk: str) -> str | None:
    composed = compose_natural_key(sheet, row)
    if composed:
        return composed
    val = row.get(nk) or row.get("product_code") or row.get("work_center_code")
    if val is None:
        return None
    return str(val)


async def ensure_ingest_tables(session: AsyncSession, tenant_id: str) -> None:
    """Bind the session to tenant RLS. Tables are created by migrations 083–084."""
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, false)"),
        {"tid": tenant_id},
    )


async def ensure_demo_tables(session: AsyncSession) -> None:
    """Back-compat alias — tables come from Alembic 083–084, not CREATE demo_*."""
    await ensure_ingest_tables(session, DEFAULT_TENANT_ID)


async def _existing_keys(session: AsyncSession, table: str, key: str, tenant_id: str) -> set[str]:
    try:
        result = await session.execute(
            text(f"SELECT {key} FROM {table} WHERE tenant_id = CAST(:tid AS uuid)"),  # noqa: S608
            {"tid": tenant_id},
        )
        return {str(r[0]) for r in result.fetchall() if r[0] is not None}
    except Exception:
        await session.rollback()
        await ensure_ingest_tables(session, tenant_id)
        return set()


async def ingest_workbook(
    session: AsyncSession,
    parsed: WorkbookParseResult,
    *,
    dry_run: bool = False,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """Validate FKs and upsert by (tenant_id, natural key). Collect all errors (batch report)."""
    tid = tenant_id or DEFAULT_TENANT_ID
    await ensure_ingest_tables(session, tid)

    # Seed key caches from already-parsed sheets (in-workbook refs) + DB
    key_cache: dict[str, set[str]] = {}
    for sheet, table in SHEET_TABLE.items():
        nk = NATURAL_KEYS.get(sheet, "")
        if not nk:
            continue
        uniq = _unique_col(sheet, table)
        db_keys = await _existing_keys(session, table, uniq, tid)
        sheet_res = parsed.sheet_results.get(sheet)
        if sheet_res and not sheet_res.skipped:
            for row in sheet_res.rows:
                val = _key_val(sheet, dict(row), nk)
                if val is not None:
                    db_keys.add(val)
                excel_val = row.get(nk) or row.get("product_code") or row.get("work_center_code")
                if excel_val is not None:
                    db_keys.add(str(excel_val))
        key_cache[table] = db_keys

    batch_errors: list[dict[str, Any]] = []
    upserted = 0
    rejected = 0
    per_sheet: list[dict[str, Any]] = []

    # Masters first, then dependents (SHEET_TABLE insertion order)
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

            key_val = _key_val(sheet, dict(row), nk)
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
                key_cache.setdefault(table, set()).add(key_val)
                continue

            try:
                await _upsert_row(session, sheet, table, nk, key_val, row, tid)
                sheet_ok += 1
                upserted += 1
                key_cache.setdefault(table, set()).add(key_val)
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
                await ensure_ingest_tables(session, tid)

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


def _extras(table: str, row: dict[str, Any], key_val: str) -> dict[str, Any]:
    if table == "cdm_ingest_product":
        return {
            "name": row.get("name") or row.get("product_name") or key_val,
            "product_type": row.get("product_type") or row.get("type"),
            "uom": row.get("uom") or row.get("uom_primary") or "EA",
        }
    if table == "cdm_ingest_work_center":
        return {
            "name": row.get("name") or row.get("work_center_name") or key_val,
            "capacity_hours": row.get("capacity_per_shift")
            or row.get("capacity_hours")
            or row.get("capacity"),
        }
    if table == "cdm_ingest_plant":
        return {"name": row.get("plant_name") or row.get("name") or key_val}
    if table == "cdm_ingest_material":
        return {"name": row.get("material_name") or row.get("name") or key_val}
    if table == "cdm_ingest_manufacturing_order":
        return {
            "product_id": row.get("product_id") or row.get("product_code"),
            "qty": row.get("quantity_planned") or row.get("qty") or row.get("quantity"),
            "feasibility": row.get("feasibility") or row.get("feasibility_score"),
            "status": row.get("status") or "planned",
            "due_date": row.get("required_date") or row.get("due_date"),
        }
    if table == "cdm_ingest_sales_order":
        return {"customer_id": row.get("customer_id")}
    if table == "cdm_ingest_purchase_order":
        return {"supplier_id": row.get("supplier_id")}
    if table == "cdm_ingest_inventory":
        return {
            "product_id": row.get("item_id") or row.get("product_id") or row.get("product_code"),
            "qty": row.get("quantity_on_hand") or row.get("qty"),
        }
    if table == "cdm_ingest_capacity_calendar":
        return {"work_center_id": row.get("work_center_id")}
    if table == "cdm_ingest_customer":
        return {"name": row.get("customer_name") or row.get("name") or key_val}
    if table == "cdm_ingest_supplier":
        return {"name": row.get("supplier_name") or row.get("name") or key_val}
    if table in ("cdm_ingest_bom", "cdm_ingest_routing"):
        return {"product_id": row.get("product_id")}
    if table == "cdm_ingest_bom_component":
        return {
            "bom_id": row.get("bom_id"),
            "component_product_id": row.get("material_id") or row.get("component_product_id"),
            "qty": row.get("quantity_per") or row.get("qty"),
        }
    if table == "cdm_ingest_routing_operation":
        return {
            "routing_id": row.get("routing_id"),
            "work_center_id": row.get("work_center_id_primary") or row.get("work_center_id"),
            "duration_hours": row.get("run_time_hours_per_unit") or row.get("duration_hours"),
            "sequence_no": row.get("operation_sequence") or row.get("sequence_no"),
        }
    if table == "cdm_ingest_calendar_shift":
        return {
            "calendar_id": row.get("calendar_id"),
            "day_of_week": row.get("day_of_week"),
            "shift_number": row.get("shift_number"),
            "shift_start_time": row.get("shift_start_time"),
            "shift_end_time": row.get("shift_end_time"),
            "break_duration_minutes": row.get("break_duration_minutes"),
            "is_working": None if row.get("is_working") is None else str(row.get("is_working")),
        }
    if table == "cdm_ingest_calendar_exception":
        return {
            "calendar_id": row.get("calendar_id"),
            "exception_date_start": row.get("exception_date_start"),
            "exception_date_end": row.get("exception_date_end"),
            "exception_type": row.get("exception_type"),
            "capacity_override_pct": row.get("capacity_override_pct"),
            "description": row.get("description"),
        }
    if table == "cdm_ingest_employee":
        return {
            "employee_code": row.get("employee_code"),
            "plant_id": row.get("plant_id"),
            "department": row.get("department"),
            "role": row.get("role"),
            "employee_name": row.get("employee_name") or row.get("name") or key_val,
            "status": row.get("status"),
            "cost_per_hour": row.get("cost_per_hour"),
        }
    if table == "cdm_ingest_employee_skill":
        return {
            "employee_id": row.get("employee_id"),
            "skill_code": row.get("skill_code"),
            "skill_name": row.get("skill_name"),
            "skill_level": row.get("skill_level"),
            "certified": None if row.get("certified") is None else str(row.get("certified")),
            "certification_expiry": row.get("certification_expiry"),
        }
    if table == "cdm_ingest_sales_order_line":
        return {
            "sales_order_id": row.get("sales_order_id"),
            "line_number": row.get("line_number"),
            "product_id": row.get("product_id"),
            "qty": row.get("quantity_ordered") or row.get("qty"),
            "status": row.get("status"),
        }
    if table == "cdm_ingest_purchase_order_line":
        return {
            "purchase_order_id": row.get("purchase_order_id"),
            "line_number": row.get("line_number"),
            "material_id": row.get("material_id"),
            "qty": row.get("quantity_ordered") or row.get("qty"),
            "status": row.get("status"),
        }
    if table == "cdm_ingest_execution_event":
        return {
            "event_type": row.get("event_type"),
            "event_datetime": row.get("event_datetime"),
            "mo_id": row.get("mo_id"),
            "operation_id": row.get("operation_id"),
            "work_center_id": row.get("work_center_id"),
            "employee_id": row.get("employee_id"),
            "quantity": row.get("quantity"),
        }
    if table in (
        "cdm_ingest_lead_time",
        "cdm_ingest_cost_data",
        "cdm_ingest_demand_forecast",
        "cdm_ingest_demand_history",
        "cdm_ingest_quality_result",
    ):
        return {}
    raise ValueError(f"Unsupported table {table}")


def _resolve_insert_key(sheet: str, table: str, nk: str, key_val: str, row: dict[str, Any]) -> tuple[str, str]:
    """Return (unique_column, unique_value) for ON CONFLICT."""
    uniq = _unique_col(sheet, table)
    if table == "cdm_ingest_routing_operation":
        routing_id = row.get("routing_id")
        op_id = row.get("operation_id") or key_val
        if routing_id:
            return uniq, f"{routing_id}:{op_id}"
    if table == "cdm_ingest_inventory":
        product_code = row.get("item_id") or row.get("product_id") or row.get("product_code") or key_val
        return uniq, f"{row.get('plant_id') or 'P'}:{product_code}:{row.get('location_code') or 'LOC'}"
    return uniq, key_val


async def _upsert_row(
    session: AsyncSession,
    sheet: str,
    table: str,
    nk: str,
    key_val: str,
    row: dict[str, Any],
    tenant_id: str,
) -> None:
    import json

    payload = json.dumps({k: v for k, v in row.items() if v is not None}, default=str)
    extra = _extras(table, row, key_val)
    uniq, uniq_val = _resolve_insert_key(sheet, table, nk, key_val, row)
    cols = {uniq: uniq_val, "tenant_id": tenant_id, **{k: v for k, v in extra.items()}}
    col_names = list(cols.keys()) + ["payload"]
    placeholders = [f":{c}" for c in cols] + ["CAST(:payload AS jsonb)"]
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c not in {uniq, "tenant_id"})
    updates = (updates + ", " if updates else "") + "payload = EXCLUDED.payload, updated_at = now()"
    sql = (
        f"INSERT INTO {table} ({', '.join(col_names)}) "
        f"VALUES ({', '.join(placeholders)}) "
        f"ON CONFLICT (tenant_id, {uniq}) DO UPDATE SET {updates}"
    )
    await session.execute(text(sql), {**cols, "payload": payload})  # noqa: S608
