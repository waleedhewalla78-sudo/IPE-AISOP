"""Multi-stage upload validation for Phase 3 Excel onboarding."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from typing import Any


FILE_SCHEMAS: dict[str, dict[str, Any]] = {
    "product_master": {
        "required": ["product_code", "name", "type", "uom"],
        "phase": 1,
        "agents": ["A2", "A4"],
    },
    "customer_master": {
        "required": ["customer_code", "name"],
        "phase": 1,
        "agents": ["A1"],
    },
    "supplier_master": {
        "required": ["supplier_code", "name"],
        "phase": 1,
        "agents": ["A2"],
    },
    "work_centre_master": {
        "required": ["work_centre_code", "name"],
        "phase": 1,
        "agents": ["A3", "A4"],
    },
    "bom": {
        "required": ["product_code", "component_code", "quantity"],
        "phase": 2,
        "agents": ["A4"],
    },
    "routing": {
        "required": ["product_code", "operation_seq", "work_centre_code"],
        "phase": 2,
        "agents": ["A3", "A4"],
    },
    "capacity_calendar": {
        "required": ["work_centre_code", "date", "shift", "available_hours"],
        "phase": 3,
        "agents": ["A3"],
    },
    "lead_time": {
        "required": ["product_code", "supplier_code", "lead_time_days"],
        "phase": 3,
        "agents": ["A2"],
    },
    "cost_data": {
        "required": ["product_code", "unit_cost"],
        "phase": 3,
        "agents": ["A5", "A6"],
    },
    "inventory": {
        "required": ["product_code", "on_hand"],
        "phase": 4,
        "agents": ["A2", "A4"],
    },
    "production_orders": {
        "required": ["mo_number", "product_code", "quantity", "planned_start", "planned_end", "status"],
        "phase": 4,
        "agents": ["A3", "A4"],
    },
    "sales_orders": {
        "required": [
            "order_number",
            "customer_code",
            "product_code",
            "quantity",
            "order_date",
            "requested_delivery",
            "status",
        ],
        "phase": 4,
        "agents": ["A1", "A4"],
    },
    "purchase_orders": {
        "required": ["po_number", "supplier_code", "product_code", "quantity"],
        "phase": 4,
        "agents": ["A2"],
    },
    "historical_otd": {
        "required": ["mo_number", "planned_end", "actual_end"],
        "phase": 5,
        "agents": ["A6"],
    },
    # Phase 8 Wave 1 — high-value operational uploads
    "demand_forecast": {
        "required": ["product_code", "period", "forecast_qty"],
        "phase": 8,
        "agents": ["A1", "A4"],
    },
    "quality_results": {
        "required": ["mo_number", "inspection_date", "result", "measured_value"],
        "phase": 8,
        "agents": ["A10"],
    },
    "sop_sales_input": {
        "required": ["product_family", "period", "sales_forecast_qty"],
        "phase": 8,
        "agents": ["A1", "A14"],
    },
}

# Aliases matching existing QA template names
ALIASES = {
    "products": "product_master",
    "customers": "customer_master",
    "suppliers": "supplier_master",
    "work_centers": "work_centre_master",
    "work_centres": "work_centre_master",
    "mrp_orders": "production_orders",
    "demand_lines": "sales_orders",
    "supply_orders": "purchase_orders",
    "forecast": "demand_forecast",
    "quality_inspection": "quality_results",
    "sop_sales": "sop_sales_input",
}


@dataclass
class RowError:
    row: int
    column: str
    value: str
    message: str
    severity: str = "error"


@dataclass
class ValidationResult:
    file_type: str
    stage_1_structure: dict[str, Any]
    stage_2_types: dict[str, Any]
    stage_3_referential: dict[str, Any]
    stage_4_business: dict[str, Any]
    total_rows: int = 0
    accepted: int = 0
    rejected: int = 0
    warnings: int = 0
    agents_triggered: list[str] = field(default_factory=list)
    errors: list[RowError] = field(default_factory=list)


def normalize_file_type(file_type: str) -> str:
    key = file_type.strip().lower().replace("-", "_").replace(" ", "_")
    return ALIASES.get(key, key)


def _invalid_format_message(filename: str, content: bytes) -> str | None:
    name = filename.lower()
    if name.endswith((".csv", ".tsv", ".txt")):
        return None
    if not name.endswith((".xlsx", ".xlsm")):
        return "Invalid file format. Expected .xlsx or .csv"
    if content[:4] != b"PK\x03\x04" and not content.startswith(b"PK\x05\x06"):
        return "Invalid file format. Expected .xlsx or .csv"
    return None


def parse_tabular(content: bytes, filename: str) -> tuple[list[str], list[dict[str, str]]]:
    fmt_err = _invalid_format_message(filename, content)
    if fmt_err:
        raise ValueError(fmt_err)
    name = filename.lower()
    if name.endswith(".xlsx") or name.endswith(".xlsm"):
        try:
            from openpyxl import load_workbook
        except ImportError as e:
            raise RuntimeError("openpyxl required for Excel uploads") from e
        wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        header_row = next(rows_iter, None)
        if not header_row:
            return [], []
        headers = [str(h).strip() if h is not None else "" for h in header_row]
        rows: list[dict[str, str]] = []
        for raw in rows_iter:
            if raw is None or all(c is None or str(c).strip() == "" for c in raw):
                continue
            row = {
                headers[i]: ("" if raw[i] is None else str(raw[i]).strip())
                for i in range(len(headers))
                if headers[i]
            }
            rows.append(row)
        return headers, rows

    # CSV / TSV fallback
    text = content.decode("utf-8-sig", errors="replace")
    dialect = csv.Sniffer().sniff(text[:2048], delimiters=",\t;")
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    headers = list(reader.fieldnames or [])
    rows = [{k: (v or "").strip() for k, v in r.items() if k} for r in reader]
    return headers, rows


class UploadValidator:
    def validate(
        self,
        file_type: str,
        content: bytes,
        filename: str,
        known_codes: dict[str, set[str]] | None = None,
    ) -> ValidationResult:
        file_type = normalize_file_type(file_type)
        schema = FILE_SCHEMAS.get(file_type)
        if not schema:
            return ValidationResult(
                file_type=file_type,
                stage_1_structure={"status": "fail", "message": f"Unknown file_type: {file_type}"},
                stage_2_types={"status": "fail", "errors": 1},
                stage_3_referential={"status": "fail", "errors": 0},
                stage_4_business={"status": "fail"},
                rejected=1,
            )

        known_codes = known_codes or {}
        try:
            headers, rows = parse_tabular(content, filename)
        except ValueError as exc:
            return ValidationResult(
                file_type=file_type,
                stage_1_structure={"status": "fail", "message": str(exc)},
                stage_2_types={"status": "fail", "errors": 0},
                stage_3_referential={"status": "fail", "errors": 0},
                stage_4_business={"status": "fail"},
                rejected=1,
            )

        required = schema["required"]
        missing = [c for c in required if c not in headers]
        stage1 = (
            {"status": "fail", "message": f"Missing columns: {', '.join(missing)}"}
            if missing
            else {"status": "pass", "message": f"All {len(required)} required columns found"}
        )
        if stage1["status"] == "pass" and not rows:
            stage1 = {"status": "pass", "message": "0 rows found. Nothing to import."}

        errors: list[RowError] = []
        warnings: list[RowError] = []
        seen_keys: dict[str, int] = {}
        if stage1["status"] == "pass" and rows:
            for idx, row in enumerate(rows, start=2):
                for col in required:
                    val = row.get(col, "")
                    if val == "":
                        errors.append(RowError(idx, col, val, f"{col} is required"))
                # Type heuristics
                for qty_col in ("quantity", "on_hand", "unit_cost", "available_hours", "lead_time_days"):
                    if qty_col in row and row[qty_col] != "":
                        try:
                            val = float(row[qty_col])
                            if qty_col in ("quantity", "on_hand") and val < 0:
                                errors.append(
                                    RowError(idx, qty_col, row[qty_col], f"{qty_col} must be non-negative")
                                )
                        except ValueError:
                            errors.append(
                                RowError(idx, qty_col, row[qty_col], f"{qty_col} must be numeric")
                            )
                pk_col = "product_code" if file_type in ("product_master", "bom") else None
                if pk_col and row.get(pk_col):
                    code = row[pk_col]
                    if code in seen_keys:
                        errors.append(
                            RowError(
                                idx,
                                pk_col,
                                code,
                                f"Duplicate {pk_col} (first seen row {seen_keys[code]})",
                            )
                        )
                    else:
                        seen_keys[code] = idx
                if file_type == "bom" and known_codes.get("products"):
                    parent = row.get("product_code", "")
                    if parent and parent not in known_codes["products"]:
                        errors.append(
                            RowError(
                                idx,
                                "product_code",
                                parent,
                                f"{parent} not found in Product Master.",
                            )
                        )
                if "priority" in row and row["priority"] and row["priority"].lower() not in (
                    "low",
                    "normal",
                    "high",
                    "urgent",
                    "",
                ):
                    warnings.append(
                        RowError(
                            idx,
                            "priority",
                            row["priority"],
                            "Unknown priority. Defaulting to 'high'",
                            severity="warning",
                        )
                    )

                # Referential checks when catalogs provided
                if "customer_code" in row and known_codes.get("customers"):
                    if row["customer_code"] and row["customer_code"] not in known_codes["customers"]:
                        errors.append(
                            RowError(
                                idx,
                                "customer_code",
                                row["customer_code"],
                                "Customer not found in master",
                            )
                        )
                if "product_code" in row and known_codes.get("products"):
                    if row["product_code"] and row["product_code"] not in known_codes["products"]:
                        errors.append(
                            RowError(
                                idx,
                                "product_code",
                                row["product_code"],
                                "Product not found in master",
                            )
                        )

        rejected_rows = {e.row for e in errors}
        accepted = max(0, len(rows) - len(rejected_rows)) if stage1["status"] == "pass" else 0
        return ValidationResult(
            file_type=file_type,
            stage_1_structure=stage1,
            stage_2_types={
                "status": "pass" if not errors else "fail",
                "errors": len([e for e in errors if e.severity == "error"]),
                "warnings": len(warnings),
                "warnings_detail": [e.__dict__ for e in warnings[:20]],
            },
            stage_3_referential={
                "status": "pass" if not any("not found" in e.message for e in errors) else "fail",
                "errors": len([e for e in errors if "not found" in e.message]),
                "errors_detail": [e.__dict__ for e in errors if "not found" in e.message][:20],
            },
            stage_4_business={"status": "pass" if stage1["status"] == "pass" else "fail"},
            total_rows=len(rows),
            accepted=accepted,
            rejected=len(rejected_rows),
            warnings=len(warnings),
            agents_triggered=list(schema.get("agents", [])),
            errors=errors + warnings,
        )
