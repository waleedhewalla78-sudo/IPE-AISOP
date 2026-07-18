#!/usr/bin/env python3
"""Regenerate QA Excel upload templates aligned to upload-svc FILE_SCHEMAS (Phases 1–8).

Writes to docs/qa/upload-templates/. Supersedes the 2026-07-12 CDM-oriented pack.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from openpyxl import Workbook
    from openpyxl.comments import Comment
except ImportError:
    print("openpyxl required", file=sys.stderr)
    raise

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "qa" / "upload-templates"

# Canonical schemas matching services/upload-svc/app/core/validator.py FILE_SCHEMAS
TEMPLATES: dict[str, dict] = {
    "product_master_upload_template.xlsx": {
        "sheet": "product_master",
        "headers": ["product_code", "name", "type", "uom", "name_ar"],
        "hints": {
            "product_code": "Required unique SKU",
            "name": "Required product name EN",
            "type": "finished|semi|raw",
            "uom": "EA, KG, etc.",
            "name_ar": "Optional Arabic name",
        },
        "rows": [
            ["FG-DT100", "Dist Transform 100kVA", "finished", "EA", "محول توزيع 100"],
            ["FG-DT250", "Dist Transform 250kVA", "finished", "EA", "محول توزيع 250"],
            ["RM-CW25", "Copper wire 25mm", "raw", "KG", "سلك نحاس"],
        ],
        "file_type": "product_master",
        "phase": 1,
    },
    "customer_master_upload_template.xlsx": {
        "sheet": "customer_master",
        "headers": ["customer_code", "name", "tier", "credit_limit"],
        "hints": {"customer_code": "Required", "name": "Required", "tier": "A|B|C optional"},
        "rows": [
            ["CUST-SEC", "Saudi Electricity", "A", 2000000],
            ["CUST-EE", "Egyptian Electric", "A", 1500000],
            ["CUST-DW", "Dubai Water", "B", 500000],
        ],
        "file_type": "customer_master",
        "phase": 1,
    },
    "supplier_master_upload_template.xlsx": {
        "sheet": "supplier_master",
        "headers": ["supplier_code", "name", "reliability_pct", "lead_time_days"],
        "hints": {"supplier_code": "Required", "name": "Required"},
        "rows": [
            ["SUP-CC", "Cairo Copper", 68, 12],
            ["SUP-NW", "National Wire Co", 92, 10],
            ["SUP-SS", "Nile Steel", 85, 14],
        ],
        "file_type": "supplier_master",
        "phase": 1,
    },
    "work_centre_master_upload_template.xlsx": {
        "sheet": "work_centre_master",
        "headers": ["work_centre_code", "name", "capacity_hrs_day"],
        "hints": {"work_centre_code": "Required", "name": "Required"},
        "rows": [
            ["WC-WND", "Winding", 16],
            ["WC-ASM", "Assembly", 16],
            ["WC-TQC", "Testing", 8],
        ],
        "file_type": "work_centre_master",
        "phase": 1,
    },
    "bom_upload_template.xlsx": {
        "sheet": "bom",
        "headers": ["product_code", "component_code", "quantity", "scrap_pct"],
        "hints": {
            "product_code": "Parent FG code (must exist in Product Master)",
            "component_code": "Component code",
            "quantity": "Numeric >= 0",
        },
        "rows": [
            ["FG-DT100", "RM-CW25", 8.5, 2],
            ["FG-DT100", "RM-CORE", 1, 0],
            ["FG-DT250", "RM-CW25", 14, 2],
        ],
        "file_type": "bom",
        "phase": 2,
    },
    "routing_upload_template.xlsx": {
        "sheet": "routing",
        "headers": ["product_code", "operation_seq", "work_centre_code", "run_minutes"],
        "hints": {"operation_seq": "Integer sequence", "work_centre_code": "Must exist"},
        "rows": [
            ["FG-DT100", 10, "WC-WND", 240],
            ["FG-DT100", 20, "WC-ASM", 120],
            ["FG-DT250", 10, "WC-WND", 360],
        ],
        "file_type": "routing",
        "phase": 2,
    },
    "capacity_calendar_upload_template.xlsx": {
        "sheet": "capacity_calendar",
        "headers": ["work_centre_code", "date", "shift", "available_hours"],
        "hints": {"date": "YYYY-MM-DD", "shift": "1|2|3", "available_hours": "Numeric >= 0"},
        "rows": [
            ["WC-WND", "2026-07-20", "1", 8],
            ["WC-WND", "2026-07-20", "2", 8],
            ["WC-ASM", "2026-07-20", "1", 8],
        ],
        "file_type": "capacity_calendar",
        "phase": 3,
    },
    "lead_time_upload_template.xlsx": {
        "sheet": "lead_time",
        "headers": ["product_code", "supplier_code", "lead_time_days"],
        "hints": {"lead_time_days": "Integer >= 0"},
        "rows": [
            ["RM-CW25", "SUP-CC", 12],
            ["RM-CW25", "SUP-NW", 10],
            ["RM-CORE", "SUP-SS", 14],
        ],
        "file_type": "lead_time",
        "phase": 3,
    },
    "cost_data_upload_template.xlsx": {
        "sheet": "cost_data",
        "headers": ["product_code", "unit_cost", "currency"],
        "hints": {"unit_cost": "Numeric >= 0"},
        "rows": [
            ["FG-DT100", 45000, "USD"],
            ["FG-DT250", 85000, "USD"],
            ["RM-CW25", 21.5, "USD"],
        ],
        "file_type": "cost_data",
        "phase": 3,
    },
    "inventory_upload_template.xlsx": {
        "sheet": "inventory",
        "headers": ["product_code", "on_hand", "location", "reserved"],
        "hints": {"on_hand": "Numeric >= 0"},
        "rows": [
            ["FG-DT100", 5, "WH-FG", 1],
            ["RM-CW25", 130, "WH-RM", 40],
            ["RM-CORE", 20, "WH-RM", 0],
        ],
        "file_type": "inventory",
        "phase": 4,
    },
    "production_orders_upload_template.xlsx": {
        "sheet": "production_orders",
        "headers": [
            "mo_number",
            "product_code",
            "quantity",
            "planned_start",
            "planned_end",
            "status",
            "priority",
        ],
        "hints": {
            "planned_start": "YYYY-MM-DD",
            "planned_end": "YYYY-MM-DD >= start",
            "status": "draft|confirmed|in_progress|done|cancelled",
            "priority": "low|normal|high|urgent",
        },
        "rows": [
            ["MO-ST-001", "FG-DT100", 3, "2026-07-20", "2026-07-28", "confirmed", "high"],
            ["MO-ST-002", "FG-DT250", 2, "2026-07-21", "2026-08-05", "confirmed", "normal"],
            ["MO-ST-003", "FG-DT100", 5, "2026-07-22", "2026-08-10", "draft", "normal"],
        ],
        "file_type": "production_orders",
        "phase": 4,
    },
    "sales_orders_upload_template.xlsx": {
        "sheet": "sales_orders",
        "headers": [
            "order_number",
            "customer_code",
            "product_code",
            "quantity",
            "order_date",
            "requested_delivery",
            "status",
        ],
        "hints": {"quantity": "Numeric >= 0", "dates": "YYYY-MM-DD"},
        "rows": [
            ["SO-2026-0289", "CUST-SEC", "FG-DT250", 10, "2026-07-10", "2026-08-10", "confirmed"],
            ["SO-2026-0290", "CUST-EE", "FG-DT100", 8, "2026-07-11", "2026-08-15", "confirmed"],
            ["SO-2026-0291", "CUST-DW", "FG-DT100", 4, "2026-07-12", "2026-08-20", "draft"],
        ],
        "file_type": "sales_orders",
        "phase": 4,
    },
    "purchase_orders_upload_template.xlsx": {
        "sheet": "purchase_orders",
        "headers": ["po_number", "supplier_code", "product_code", "quantity", "unit_price", "expected_delivery"],
        "hints": {"quantity": "Numeric >= 0"},
        "rows": [
            ["PO-1001", "SUP-CC", "RM-CW25", 200, 21.5, "2026-07-30"],
            ["PO-1002", "SUP-NW", "RM-CW25", 80, 22.0, "2026-07-28"],
            ["PO-1003", "SUP-SS", "RM-CORE", 15, 1200, "2026-08-05"],
        ],
        "file_type": "purchase_orders",
        "phase": 4,
    },
    "historical_otd_upload_template.xlsx": {
        "sheet": "historical_otd",
        "headers": ["mo_number", "planned_end", "actual_end", "delay_days"],
        "hints": {"planned_end": "YYYY-MM-DD", "actual_end": "YYYY-MM-DD"},
        "rows": [
            ["MO-ST-008", "2026-06-15", "2026-06-18", 3],
            ["MO-ST-009", "2026-06-20", "2026-06-20", 0],
            ["MO-ST-010", "2026-06-25", "2026-06-29", 4],
        ],
        "file_type": "historical_otd",
        "phase": 5,
    },
    "demand_forecast_upload_template.xlsx": {
        "sheet": "demand_forecast",
        "headers": ["product_code", "period", "forecast_qty", "source"],
        "hints": {
            "period": "YYYY-MM or week label",
            "forecast_qty": "Numeric >= 0",
            "source": "Optional statistical|sales|marketing",
        },
        "rows": [
            ["FG-DT100", "2026-08", 24, "statistical"],
            ["FG-DT100", "2026-09", 28, "sales"],
            ["FG-DT250", "2026-08", 15, "statistical"],
        ],
        "file_type": "demand_forecast",
        "phase": 8,
    },
    "quality_results_upload_template.xlsx": {
        "sheet": "quality_results",
        "headers": ["mo_number", "inspection_date", "result", "measured_value", "defect_type"],
        "hints": {
            "result": "pass|fail|on_hold",
            "inspection_date": "YYYY-MM-DD",
            "measured_value": "Numeric",
        },
        "rows": [
            ["MO-ST-008", "2026-07-15", "fail", 0.15, "winding_tension"],
            ["MO-ST-009", "2026-07-15", "pass", 0.98, ""],
            ["MO-ST-001", "2026-07-16", "pass", 0.99, ""],
        ],
        "file_type": "quality_results",
        "phase": 8,
    },
    "sop_sales_input_upload_template.xlsx": {
        "sheet": "sop_sales_input",
        "headers": ["product_family", "period", "sales_forecast_qty", "rationale"],
        "hints": {
            "product_family": "e.g. DT100, DT250",
            "period": "YYYY-MM",
            "sales_forecast_qty": "Numeric >= 0",
        },
        "rows": [
            ["DT100", "2026-08", 28, "Egyptian Electric expansion"],
            ["DT250", "2026-08", 18, "Saudi program"],
            ["PT500", "2026-08", 6, "Tender pipeline"],
        ],
        "file_type": "sop_sales_input",
        "phase": 8,
    },
    "project_plan_upload_template.xlsx": {
        "sheet": "ProjectPlan",
        "headers": [
            "MO_ID",
            "OPERATION_SEQ",
            "WORK_CENTER_CODE",
            "PLANNED_START",
            "PLANNED_END",
            "DURATION_HRS",
        ],
        "hints": {
            "MO_ID": "Must match seeded erp_mo_id (e.g. MO-ST-001)",
            "WORK_CENTER_CODE": "Must match WC code",
            "note": "UI upload: Planning → Schedule (.xlsx only, max 5MB)",
        },
        "rows": [
            ["MO-ST-001", 10, "WC-WND", "2026-07-20", "2026-07-22", 16],
            ["MO-ST-001", 20, "WC-ASM", "2026-07-22", "2026-07-24", 12],
            ["MO-ST-002", 10, "WC-WND", "2026-07-23", "2026-07-26", 24],
        ],
        "file_type": "project_plan (cap-svc)",
        "phase": "Schedule UI",
    },
}


def _write(name: str, meta: dict) -> Path:
    wb = Workbook()
    # Data sheet MUST be active/first — upload-svc parse_tabular uses wb.active
    ws = wb.active
    ws.title = meta["sheet"][:31]
    headers = meta["headers"]
    ws.append(headers)
    hints = meta.get("hints", {})
    for col_idx, h in enumerate(headers, start=1):
        tip = hints.get(h) or hints.get("note") or hints.get("dates")
        if tip:
            ws.cell(1, col_idx).comment = Comment(str(tip), "IPE")
    for row in meta["rows"]:
        ws.append(row)
    # README after data sheet (never index 0) so uploads keep working
    readme = wb.create_sheet("README")
    readme.append(["file_type", meta["file_type"]])
    readme.append(["phase", meta["phase"]])
    readme.append(["aligned_to", "upload-svc FILE_SCHEMAS (validator.py) as of 2026-07-18"])
    readme.append(["note", "Headers MUST match upload-svc (lowercase). Old 2026-07-12 templates used PRODUCT_CODE style."])
    readme.append(["ui", "Platform → Data Upload (/platform/upload) — validate path; project plan via Planning → Schedule"])
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    wb.save(path)
    return path


def main() -> int:
    # Remove obsolete CDM-named templates from 2026-07-12 pack (superseded names)
    obsolete = [
        "products_upload_template.xlsx",
        "customers_upload_template.xlsx",
        "suppliers_upload_template.xlsx",
        "work_centers_upload_template.xlsx",
        "bom_routing_upload_template.xlsx",
        "mrp_orders_upload_template.xlsx",
        "demand_lines_upload_template.xlsx",
        "supply_orders_upload_template.xlsx",
        "operators_upload_template.xlsx",
        # keep: project_plan (regen), tariff, odoo reference
    ]
    for old in obsolete:
        p = OUT / old
        if p.exists():
            p.unlink()
            print(f"removed obsolete {old}")

    written = []
    for name, meta in TEMPLATES.items():
        path = _write(name, meta)
        written.append(path.name)
        print(f"OK {path.name}")

    # Preserve tariff + odoo reference if present (not upload-svc types)
    for keep in ("tariff_matrix_upload_template.xlsx", "odoo_sync_entities_reference.xlsx"):
        if (OUT / keep).exists():
            print(f"kept {keep}")

    readme = OUT / "README.md"
    lines = [
        "# IPE Upload Templates (aligned to upload-svc)",
        "",
        "**Regenerated:** 2026-07-18",
        "**Source of truth:** `services/upload-svc/app/core/validator.py` `FILE_SCHEMAS`",
        "",
        "## Important — superseded 2026-07-12 pack",
        "",
        "The July 12 templates used CDM/seed-style **UPPER_SNAKE** headers (`PRODUCT_CODE`, …).",
        "Data Upload Center / upload-svc requires **lowercase** headers (`product_code`, …).",
        "This pack matches upload-svc **Phases 1–5 + Phase 8** types.",
        "",
        "## How data loads",
        "",
        "| Path | Mechanism | Persists? |",
        "|------|-----------|-----------|",
        "| Data Upload Center | `POST /api/v1/upload/{file_type}` | Validate + wizard state (**not** full CDM row import) |",
        "| Project plan | Schedule UI → `.xlsx` | **Yes** (cap-svc) |",
        "| SQL seed | `seed-data.ps1` / `seed-startrans-demo.ps1` | **Yes** |",
        "| Odoo sync | Platform → Odoo Connections | **Yes** when live (PH1-02 OPEN → mock) |",
        "| Tariff matrix | Template only | **No HTTP upload** |",
        "",
        "## Template index",
        "",
        "| File | file_type | Phase | Required columns |",
        "|------|-----------|-------|------------------|",
    ]
    for name, meta in TEMPLATES.items():
        req = ", ".join(meta["headers"][: len(meta["headers"])])
        # only required from schema - list first N matching FILE_SCHEMAS required
        lines.append(f"| `{name}` | `{meta['file_type']}` | {meta['phase']} | {req} |")
    lines.extend(
        [
            "",
            "| `tariff_matrix_upload_template.xlsx` | *(unwired)* | — | Parser only |",
            "| `odoo_sync_entities_reference.xlsx` | *(reference)* | — | Not an upload |",
            "",
            "## UI",
            "",
            "1. Open http://localhost:8082 → login `Ahmed@nour` / `admin`",
            "2. **Platform → Data Upload** — pick file_type matching the template",
            "3. **Planning → Schedule** — Upload Project Plan (`project_plan_upload_template.xlsx`)",
            "",
            "## Regenerator",
            "",
            "```powershell",
            "cd E:\\AISOP\\ipe",
            ".\\.venv\\Scripts\\python.exe scripts\\generate_upload_templates.py",
            "```",
            "",
        ]
    )
    readme.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote README + {len(written)} templates -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
