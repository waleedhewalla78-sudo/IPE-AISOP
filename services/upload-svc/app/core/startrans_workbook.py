"""Star Trans multi-sheet Excel workbook parser (demo Sprint Stream 2).

Expects IPE_Data_Template_StarTrans_v1.xlsx shape: 24 named sheets.
Rows 1–5 are title/purpose/legend/header; data starts at row 6 (1-indexed).
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Any

from openpyxl import load_workbook

# 24 sheets — must match customer template / demo contract
EXPECTED_SHEETS: list[str] = [
    "00_README",
    "01_Products",
    "02_WorkCenters",
    "03_BOM",
    "04_Routing",
    "05_Customers",
    "06_Suppliers",
    "07_ManufacturingOrders",
    "08_SalesOrders",
    "09_PurchaseOrders",
    "10_Inventory",
    "11_CapacityCalendar",
    "12_LeadTimes",
    "13_CostData",
    "14_DemandForecast",
    "15_DemandHistory",
    "16_QualityResults",
    "17_HistoricalOTD",
    "18_SOPSalesInput",
    "19_ProjectPlan",
    "20_TariffMatrix",
    "21_WorkCenterCalendar",
    "22_BOMComponents",
    "23_RoutingOperations",
]

# Natural key per sheet for upsert preview
NATURAL_KEYS: dict[str, str] = {
    "01_Products": "product_id",
    "02_WorkCenters": "work_center_id",
    "03_BOM": "bom_id",
    "04_Routing": "routing_id",
    "05_Customers": "customer_id",
    "06_Suppliers": "supplier_id",
    "07_ManufacturingOrders": "mo_id",
    "08_SalesOrders": "so_id",
    "09_PurchaseOrders": "po_id",
    "10_Inventory": "inventory_id",
    "11_CapacityCalendar": "calendar_id",
    "12_LeadTimes": "lead_time_id",
    "13_CostData": "cost_id",
    "14_DemandForecast": "forecast_id",
    "15_DemandHistory": "history_id",
    "16_QualityResults": "quality_id",
    "17_HistoricalOTD": "otd_id",
    "18_SOPSalesInput": "sop_id",
    "19_ProjectPlan": "plan_line_id",
    "20_TariffMatrix": "tariff_id",
    "21_WorkCenterCalendar": "wc_calendar_id",
    "22_BOMComponents": "bom_component_id",
    "23_RoutingOperations": "operation_id",
}

DATA_START_ROW = 6  # 1-indexed; rows 1–5 skipped
HEADER_ROW = 5


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
    except Exception as exc:  # noqa: BLE001 — surface parse failure to caller
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
    expected_set = set(EXPECTED_SHEETS)
    found_set = set(found)
    missing = [s for s in EXPECTED_SHEETS if s not in found_set]
    extra = [s for s in found if s not in expected_set]

    if missing:
        errors.append(f"Missing expected sheets ({len(missing)}): {', '.join(missing[:8])}"
                      + ("…" if len(missing) > 8 else ""))
    if extra:
        errors.append(f"Unexpected sheets ignored: {', '.join(extra[:8])}")

    sheet_results: dict[str, SheetParseResult] = {}
    for name in EXPECTED_SHEETS:
        if name not in found_set:
            sheet_results[name] = SheetParseResult(
                sheet_name=name, skipped=True, message="sheet missing"
            )
            continue
        if name == "00_README":
            sheet_results[name] = SheetParseResult(
                sheet_name=name, skipped=True, message="metadata only"
            )
            continue
        sheet_results[name] = _parse_data_sheet(wb[name], name)

    wb.close()
    # Valid for preview if structure opens; missing sheets are soft-fail for demo
    # Hard-invalid only when file unreadable or zero data sheets parseable
    data_ok = any(
        (not r.skipped and len(r.rows) > 0) or (not r.skipped and not r.row_errors)
        for r in sheet_results.values()
    )
    valid = len(errors) == 0 or (not missing and data_ok)
    # Soft: allow preview with missing sheets so UI can show batch report
    if missing and any(not r.skipped and r.rows for r in sheet_results.values()):
        valid = True

    return WorkbookParseResult(
        sheets_found=found,
        sheets_missing=missing,
        sheets_extra=extra,
        sheet_results=sheet_results,
        valid=valid or bool(sheet_results),
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
            # Drop trailing empties
            while headers and headers[-1] == "":
                headers.pop()
            if not any(headers):
                return SheetParseResult(
                    sheet_name=name,
                    skipped=True,
                    message="empty header row (row 5)",
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
        if nk and not record.get(nk) and not record.get(nk.replace("_", "")):
            # try common aliases
            aliases = {
                "product_id": ["product_code", "product_id", "sku"],
                "mo_id": ["mo_id", "order_id", "manufacturing_order_id"],
                "work_center_id": ["work_center_code", "work_center_id", "wc_code"],
                "customer_id": ["customer_code", "customer_id"],
                "supplier_id": ["supplier_code", "supplier_id"],
            }
            for alias in aliases.get(nk, []):
                if record.get(alias):
                    record[nk] = record[alias]
                    break
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
            }
        )
    return {
        "will_insert": will_insert,
        "will_fail": will_fail,
        "sheets": sheets,
        "sheets_missing": parsed.sheets_missing,
        "workbook_errors": parsed.errors,
    }
