"""Star Trans multi-sheet Excel workbook parser (demo Sprint Stream 2).

Canonical file: docs/demo-data/startrans/IPE_Data_Template_StarTrans_v1.xlsx
Layout per sheet: row 1 title, 2 purpose, 3 legend, 4 headers, data from row 5.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Any

from openpyxl import load_workbook

# Exact 24 sheet names from IPE_Data_Template_StarTrans_v1.xlsx
EXPECTED_SHEETS: list[str] = [
    "README",
    "01_Plants",
    "02_WorkCenters",
    "03a_Calendars",
    "03b_CalendarShifts",
    "03c_CalendarExceptions",
    "04_Products",
    "05_Materials",
    "06a_BOMHeaders",
    "06b_BOMLines",
    "07a_RoutingHeaders",
    "07b_RoutingOperations",
    "08_Suppliers",
    "09_Customers",
    "10a_Employees",
    "10b_EmployeeSkills",
    "11a_SalesOrderHeaders",
    "11b_SalesOrderLines",
    "12_ManufacturingOrders",
    "13a_PurchaseOrderHeaders",
    "13b_PurchaseOrderLines",
    "14_Inventory",
    "15_Forecasts",
    "16_ExecutionEvents",
]

# Priority sheets for Aug 18 demo cycle (customer email)
PRIORITY_SHEETS: list[str] = [
    "01_Plants",
    "02_WorkCenters",
    "04_Products",
    "05_Materials",
    "09_Customers",
    "12_ManufacturingOrders",
]

# Natural key per sheet for upsert preview (synthetic keys composed from Excel cols)
NATURAL_KEYS: dict[str, str] = {
    "01_Plants": "plant_id",
    "02_WorkCenters": "work_center_id",
    "03a_Calendars": "calendar_id",
    "03b_CalendarShifts": "shift_id",
    "03c_CalendarExceptions": "exception_id",
    "04_Products": "product_id",
    "05_Materials": "material_id",
    "06a_BOMHeaders": "bom_id",
    "06b_BOMLines": "bom_component_id",
    "07a_RoutingHeaders": "routing_id",
    "07b_RoutingOperations": "operation_id",
    "08_Suppliers": "supplier_id",
    "09_Customers": "customer_id",
    "10a_Employees": "employee_id",
    "10b_EmployeeSkills": "employee_skill_id",
    "11a_SalesOrderHeaders": "sales_order_id",
    "11b_SalesOrderLines": "so_line_id",
    "12_ManufacturingOrders": "mo_id",
    "13a_PurchaseOrderHeaders": "purchase_order_id",
    "13b_PurchaseOrderLines": "po_line_id",
    "14_Inventory": "item_id",
    "15_Forecasts": "forecast_id",
    "16_ExecutionEvents": "event_id",
}

# Sheets whose Excel row is not a single-column PK — join these fields with ":"
_COMPOSITE_PARTS: dict[str, tuple[str, ...]] = {
    "03b_CalendarShifts": ("calendar_id", "day_of_week", "shift_number"),
    "03c_CalendarExceptions": ("calendar_id", "exception_date_start", "exception_type"),
    "06b_BOMLines": ("bom_id", "line_number"),
    "10b_EmployeeSkills": ("employee_id", "skill_code"),
    "11b_SalesOrderLines": ("sales_order_id", "line_number"),
    "13b_PurchaseOrderLines": ("purchase_order_id", "line_number"),
    "16_ExecutionEvents": ("event_type", "event_datetime", "mo_id", "operation_id"),
}


def compose_natural_key(sheet: str, record: dict[str, Any]) -> str | None:
    """Fill/return the unique key for a sheet row (composite sheets included)."""
    nk = NATURAL_KEYS.get(sheet)
    parts = _COMPOSITE_PARTS.get(sheet)
    if parts:
        if record.get(parts[0]) is None or str(record.get(parts[0])).strip() == "":
            return None
        key = ":".join("" if record.get(p) is None else str(record.get(p)) for p in parts)
        if nk:
            record[nk] = key
        return key
    if not nk:
        return None
    val = record.get(nk)
    return str(val) if val is not None and str(val).strip() != "" else None

HEADER_ROW = 4  # 1-indexed column names
DATA_START_ROW = 5  # first data row


@dataclass
class SheetParseResult:
    sheet_name: str
    headers: list[str] = field(default_factory=list)
    rows: list[dict[str, Any]] = field(default_factory=list)
    row_errors: list[dict[str, Any]] = field(default_factory=list)
    skipped: bool = False
    message: str = ""


@dataclass
class WorkbookParseResult:
    sheets_found: list[str]
    sheets_missing: list[str]
    sheets_extra: list[str]
    sheet_results: dict[str, SheetParseResult]
    valid: bool
    errors: list[str] = field(default_factory=list)


def _norm_header(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower().replace(" ", "_")


def _cell_str(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def parse_workbook(content: bytes, filename: str = "workbook.xlsx") -> WorkbookParseResult:
    """Parse multi-sheet Star Trans workbook; collect all sheet-level errors."""
    errors: list[str] = []
    if not filename.lower().endswith((".xlsx", ".xlsm")):
        errors.append(f"Unsupported file type: {filename} (expect .xlsx)")
        return WorkbookParseResult(
            sheets_found=[],
            sheets_missing=list(EXPECTED_SHEETS),
            sheets_extra=[],
            sheet_results={},
            valid=False,
            errors=errors,
        )

    try:
        wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Cannot open workbook: {exc}")
        return WorkbookParseResult(
            sheets_found=[],
            sheets_missing=list(EXPECTED_SHEETS),
            sheets_extra=[],
            sheet_results={},
            valid=False,
            errors=errors,
        )

    found = list(wb.sheetnames)
    found_set = set(found)
    missing = [s for s in EXPECTED_SHEETS if s not in found_set]
    extra = [s for s in found if s not in set(EXPECTED_SHEETS)]

    if missing:
        errors.append(
            f"Missing expected sheets ({len(missing)}): {', '.join(missing[:8])}"
            + ("…" if len(missing) > 8 else "")
        )
    if extra:
        errors.append(f"Unexpected sheets ignored: {', '.join(extra[:8])}")

    sheet_results: dict[str, SheetParseResult] = {}
    for name in EXPECTED_SHEETS:
        if name not in found_set:
            sheet_results[name] = SheetParseResult(
                sheet_name=name, skipped=True, message="sheet missing"
            )
            continue
        if name == "README":
            sheet_results[name] = SheetParseResult(
                sheet_name=name, skipped=True, message="metadata only"
            )
            continue
        sheet_results[name] = _parse_data_sheet(wb[name], name)

    wb.close()

    # Soft-valid when at least priority sheets have rows (demo-friendly)
    priority_ok = any(
        (r := sheet_results.get(s)) and not r.skipped and r.rows for s in PRIORITY_SHEETS
    )
    valid = (not missing and not errors) or priority_ok or bool(
        any(not r.skipped and r.rows for r in sheet_results.values())
    )

    return WorkbookParseResult(
        sheets_found=found,
        sheets_missing=missing,
        sheets_extra=extra,
        sheet_results=sheet_results,
        valid=valid,
        errors=errors,
    )


def _parse_data_sheet(ws: Any, name: str) -> SheetParseResult:
    rows_iter = ws.iter_rows(values_only=True)
    headers: list[str] = []
    data_rows: list[dict[str, Any]] = []
    row_errors: list[dict[str, Any]] = []

    for idx, raw in enumerate(rows_iter, start=1):
        if idx < HEADER_ROW:
            continue
        if idx == HEADER_ROW:
            headers = [_norm_header(c) for c in raw]
            while headers and headers[-1] == "":
                headers.pop()
            if not any(headers):
                return SheetParseResult(
                    sheet_name=name,
                    skipped=True,
                    message="empty header row (row 4)",
                )
            continue
        if idx < DATA_START_ROW:
            continue
        if raw is None or all(c is None or str(c).strip() == "" for c in raw):
            continue

        record: dict[str, Any] = {}
        for col_i, key in enumerate(headers):
            if not key:
                continue
            val = _cell_str(raw[col_i]) if col_i < len(raw) else None
            record[key] = val

        nk = NATURAL_KEYS.get(name)
        compose_natural_key(name, record)
        if nk and not record.get(nk):
            aliases = {
                "product_id": ["product_code", "product_id", "sku"],
                "mo_id": ["mo_id", "mo_number", "order_id"],
                "work_center_id": ["work_center_code", "work_center_id", "wc_code"],
                "customer_id": ["customer_code", "customer_id"],
                "supplier_id": ["supplier_code", "supplier_id"],
                "material_id": ["material_code", "material_id"],
                "plant_id": ["plant_code", "plant_id"],
                "item_id": ["item_id", "material_id", "product_id"],
                "employee_id": ["employee_code", "employee_id"],
            }
            for alias in aliases.get(nk, []):
                if record.get(alias):
                    record[nk] = record[alias]
                    break
            compose_natural_key(name, record)
            if nk and not record.get(nk):
                row_errors.append(
                    {
                        "sheet": name,
                        "row": idx,
                        "column": nk,
                        "message": f"Missing natural key {nk}",
                        "severity": "error",
                    }
                )
                continue

        data_rows.append(record)

    return SheetParseResult(
        sheet_name=name,
        headers=headers,
        rows=data_rows,
        row_errors=row_errors,
    )


def preview_counts(parsed: WorkbookParseResult) -> dict[str, Any]:
    """Summarize insert vs fail for UI preview."""
    sheets: list[dict[str, Any]] = []
    will_insert = 0
    will_fail = 0
    for name in EXPECTED_SHEETS:
        r = parsed.sheet_results.get(name)
        if not r or r.skipped:
            sheets.append(
                {
                    "sheet": name,
                    "insert": 0,
                    "fail": 0,
                    "skipped": True,
                    "message": r.message if r else "missing",
                    "priority": name in PRIORITY_SHEETS,
                }
            )
            continue
        insert = len(r.rows)
        fail = len(r.row_errors)
        will_insert += insert
        will_fail += fail
        sheets.append(
            {
                "sheet": name,
                "insert": insert,
                "fail": fail,
                "skipped": False,
                "natural_key": NATURAL_KEYS.get(name),
                "priority": name in PRIORITY_SHEETS,
            }
        )
    return {
        "will_insert": will_insert,
        "will_fail": will_fail,
        "sheets": sheets,
        "sheets_missing": parsed.sheets_missing,
        "workbook_errors": parsed.errors,
        "priority_sheets": PRIORITY_SHEETS,
    }
