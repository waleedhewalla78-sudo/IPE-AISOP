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
        "headers": [
            "product_code",
            "product_group",
            "product_type",
            "short_name",
            "full_name",
            "uom",
            "main_storage_location",
            "name_ar",
            "standard_cost",
            "currency",
            "safety_stock",
            "reorder_point",
            "lead_time_days",
            "abc_class",
            "active",
            "weight_kg",
            "hs_code",
        ],
        "hints": {
            "product_code": "Unique SKU / item code (required)",
            "product_group": "Family/group e.g. DT, PT, RM-CU (required)",
            "product_type": "finished|semi|raw (required)",
            "short_name": "Short display name (required)",
            "full_name": "Full commercial/technical name (required)",
            "uom": "Unit of measure: EA, KG, M, L (required)",
            "main_storage_location": "Default warehouse/bin e.g. WH-FG (required)",
            "name_ar": "Optional Arabic name",
            "abc_class": "A|B|C optional",
            "active": "true|false",
        },
        "rows": [
            [
                "FG-DT100",
                "DT",
                "finished",
                "DT100",
                "Distribution Transformer 100kVA Oil-Immersed",
                "EA",
                "WH-FG",
                "محول توزيع 100 ك.ف.أ",
                45000,
                "USD",
                2,
                1,
                21,
                "A",
                "true",
                680,
                "850421",
            ],
            [
                "FG-DT250",
                "DT",
                "finished",
                "DT250",
                "Distribution Transformer 250kVA Oil-Immersed",
                "EA",
                "WH-FG",
                "محول توزيع 250 ك.ف.أ",
                85000,
                "USD",
                1,
                1,
                28,
                "A",
                "true",
                1250,
                "850421",
            ],
            [
                "RM-CW25",
                "RM-CU",
                "raw",
                "CuWire25",
                "Copper Winding Wire 25mm2",
                "KG",
                "WH-RM",
                "سلك نحاس 25 مم",
                21.5,
                "USD",
                50,
                100,
                12,
                "B",
                "true",
                0,
                "740819",
            ],
            [
                "SF-CORE100",
                "CORE",
                "semi",
                "Core100",
                "Magnetic Core Assembly 100kVA",
                "EA",
                "WH-WIP",
                "قلب مغناطيسي 100",
                8200,
                "USD",
                3,
                2,
                7,
                "B",
                "true",
                210,
                "",
            ],
        ],
        "file_type": "product_master",
        "phase": 1,
    },
    "customer_master_upload_template.xlsx": {
        "sheet": "customer_master",
        "headers": [
            "customer_code",
            "name",
            "name_ar",
            "tier",
            "country",
            "city",
            "currency",
            "credit_limit",
            "payment_terms",
            "contact_name",
            "contact_email",
            "contact_phone",
            "tax_id",
            "active",
        ],
        "hints": {
            "customer_code": "Required unique code",
            "name": "Legal / trading name (required)",
            "tier": "A|B|C",
            "country": "ISO country or name (required)",
            "currency": "USD|EGP|SAR|AED (required)",
        },
        "rows": [
            [
                "CUST-SEC",
                "Saudi Electricity Company",
                "الشركة السعودية للكهرباء",
                "A",
                "SA",
                "Riyadh",
                "SAR",
                2000000,
                "Net30",
                "Omar Al-Harbi",
                "omar@sec.example",
                "+966500000001",
                "SA-3001234567",
                "true",
            ],
            [
                "CUST-EE",
                "Egyptian Electric",
                "الكهرباء المصرية",
                "A",
                "EG",
                "Cairo",
                "EGP",
                1500000,
                "Net45",
                "Mona Hassan",
                "mona@ee.example",
                "+201000000002",
                "EG-123456789",
                "true",
            ],
            [
                "CUST-DW",
                "Dubai Water & Electricity",
                "مياه وكهرباء دبي",
                "B",
                "AE",
                "Dubai",
                "AED",
                500000,
                "Net30",
                "Ali Rahman",
                "ali@dw.example",
                "+971500000003",
                "AE-987654321",
                "true",
            ],
        ],
        "file_type": "customer_master",
        "phase": 1,
    },
    "supplier_master_upload_template.xlsx": {
        "sheet": "supplier_master",
        "headers": [
            "supplier_code",
            "name",
            "name_ar",
            "lead_time_days",
            "country",
            "city",
            "currency",
            "reliability_pct",
            "payment_terms",
            "contact_name",
            "contact_email",
            "min_order_qty",
            "active",
        ],
        "hints": {
            "supplier_code": "Required unique code",
            "lead_time_days": "Default procurement LT (required)",
            "country": "Required",
            "currency": "Required",
        },
        "rows": [
            [
                "SUP-CC",
                "Cairo Copper",
                "نحاس القاهرة",
                12,
                "EG",
                "Cairo",
                "USD",
                68,
                "Net30",
                "Hassan Ali",
                "h.ali@cairocopper.example",
                100,
                "true",
            ],
            [
                "SUP-NW",
                "National Wire Co",
                "الأسلاك الوطنية",
                10,
                "EG",
                "Alexandria",
                "USD",
                92,
                "Net21",
                "Sara Nabil",
                "sara@natwire.example",
                50,
                "true",
            ],
            [
                "SUP-SS",
                "Nile Steel",
                "صلب النيل",
                14,
                "EG",
                "Helwan",
                "EGP",
                85,
                "Net45",
                "Karim Fathy",
                "karim@nilesteel.example",
                5,
                "true",
            ],
        ],
        "file_type": "supplier_master",
        "phase": 1,
    },
    "work_centre_master_upload_template.xlsx": {
        "sheet": "work_centre_master",
        "headers": [
            "work_centre_code",
            "name",
            "name_ar",
            "capacity_hrs_day",
            "location",
            "shifts_per_day",
            "efficiency_pct",
            "calendar_code",
            "cost_per_hour",
            "active",
        ],
        "hints": {
            "work_centre_code": "Required WC code",
            "capacity_hrs_day": "Available hours/day (required)",
            "location": "Plant / bay (required)",
            "efficiency_pct": "0-100",
        },
        "rows": [
            ["WC-WND", "Winding", "اللف", 16, "Bay-A", 2, 85, "CAL-STD", 45, "true"],
            ["WC-ASM", "Assembly", "التجميع", 16, "Bay-B", 2, 90, "CAL-STD", 40, "true"],
            ["WC-TQC", "Testing & QC", "الاختبار", 8, "Lab-1", 1, 95, "CAL-STD", 55, "true"],
        ],
        "file_type": "work_centre_master",
        "phase": 1,
    },
    "bom_upload_template.xlsx": {
        "sheet": "bom",
        "headers": [
            "product_code",
            "component_code",
            "quantity",
            "uom",
            "scrap_pct",
            "operation_seq",
            "effective_from",
            "effective_to",
        ],
        "hints": {
            "product_code": "Parent FG/SFG code (must exist in Product Master)",
            "component_code": "Component code",
            "quantity": "Numeric >= 0",
            "uom": "Component UoM",
        },
        "rows": [
            ["FG-DT100", "RM-CW25", 8.5, "KG", 2, 10, "2026-01-01", ""],
            ["FG-DT100", "SF-CORE100", 1, "EA", 0, 20, "2026-01-01", ""],
            ["FG-DT250", "RM-CW25", 14, "KG", 2, 10, "2026-01-01", ""],
        ],
        "file_type": "bom",
        "phase": 2,
    },
    "routing_upload_template.xlsx": {
        "sheet": "routing",
        "headers": [
            "product_code",
            "operation_seq",
            "work_centre_code",
            "run_minutes",
            "setup_minutes",
            "description",
            "overlap_pct",
        ],
        "hints": {
            "operation_seq": "Integer sequence 10/20/30…",
            "work_centre_code": "Must exist in work centre master",
            "run_minutes": "Run time minutes",
        },
        "rows": [
            ["FG-DT100", 10, "WC-WND", 240, 30, "LV/HV winding", 0],
            ["FG-DT100", 20, "WC-ASM", 120, 20, "Tank assembly", 10],
            ["FG-DT250", 10, "WC-WND", 360, 40, "LV/HV winding", 0],
        ],
        "file_type": "routing",
        "phase": 2,
    },
    "capacity_calendar_upload_template.xlsx": {
        "sheet": "capacity_calendar",
        "headers": ["work_centre_code", "date", "shift", "available_hours", "overtime_hours", "notes"],
        "hints": {"date": "YYYY-MM-DD", "shift": "1|2|3", "available_hours": "Numeric >= 0"},
        "rows": [
            ["WC-WND", "2026-07-20", "1", 8, 0, ""],
            ["WC-WND", "2026-07-20", "2", 8, 2, "Peak load OT"],
            ["WC-ASM", "2026-07-20", "1", 8, 0, ""],
        ],
        "file_type": "capacity_calendar",
        "phase": 3,
    },
    "lead_time_upload_template.xlsx": {
        "sheet": "lead_time",
        "headers": ["product_code", "supplier_code", "lead_time_days", "min_qty", "transport_mode", "incoterm"],
        "hints": {"lead_time_days": "Integer >= 0"},
        "rows": [
            ["RM-CW25", "SUP-CC", 12, 100, "truck", "EXW"],
            ["RM-CW25", "SUP-NW", 10, 50, "truck", "DDP"],
            ["SF-CORE100", "SUP-SS", 14, 5, "truck", "FCA"],
        ],
        "file_type": "lead_time",
        "phase": 3,
    },
    "cost_data_upload_template.xlsx": {
        "sheet": "cost_data",
        "headers": ["product_code", "unit_cost", "currency", "cost_type", "effective_from", "standard_cost"],
        "hints": {"unit_cost": "Numeric >= 0", "cost_type": "standard|actual|purchase"},
        "rows": [
            ["FG-DT100", 45000, "USD", "standard", "2026-01-01", 45000],
            ["FG-DT250", 85000, "USD", "standard", "2026-01-01", 85000],
            ["RM-CW25", 21.5, "USD", "purchase", "2026-07-01", 20],
        ],
        "file_type": "cost_data",
        "phase": 3,
    },
    "inventory_upload_template.xlsx": {
        "sheet": "inventory",
        "headers": ["product_code", "on_hand", "location", "reserved", "available", "lot_number", "uom"],
        "hints": {"on_hand": "Numeric >= 0", "location": "Warehouse / bin"},
        "rows": [
            ["FG-DT100", 5, "WH-FG", 1, 4, "LOT-FG-001", "EA"],
            ["RM-CW25", 130, "WH-RM", 40, 90, "LOT-CU-088", "KG"],
            ["SF-CORE100", 20, "WH-WIP", 0, 20, "LOT-CORE-12", "EA"],
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
            "work_centre_code",
            "customer_code",
            "sales_order",
        ],
        "hints": {
            "planned_start": "YYYY-MM-DD",
            "planned_end": "YYYY-MM-DD >= start",
            "status": "draft|confirmed|in_progress|done|cancelled",
            "priority": "low|normal|high|urgent",
        },
        "rows": [
            ["MO-ST-001", "FG-DT100", 3, "2026-07-20", "2026-07-28", "confirmed", "high", "WC-WND", "CUST-EE", "SO-2026-0290"],
            ["MO-ST-002", "FG-DT250", 2, "2026-07-21", "2026-08-05", "confirmed", "normal", "WC-WND", "CUST-SEC", "SO-2026-0289"],
            ["MO-ST-003", "FG-DT100", 5, "2026-07-22", "2026-08-10", "draft", "normal", "WC-ASM", "", ""],
        ],
        "file_type": "production_orders",
        "phase": 4,
    },
    "sales_orders_upload_template.xlsx": {
        "sheet": "sales_orders",
        "headers": [
            "order_number",
            "line_number",
            "customer_code",
            "product_code",
            "quantity",
            "uom",
            "unit_price",
            "currency",
            "order_date",
            "requested_delivery",
            "status",
            "warehouse",
        ],
        "hints": {"quantity": "Numeric >= 0", "dates": "YYYY-MM-DD"},
        "rows": [
            ["SO-2026-0289", 10, "CUST-SEC", "FG-DT250", 10, "EA", 92000, "SAR", "2026-07-10", "2026-08-10", "confirmed", "WH-FG"],
            ["SO-2026-0290", 10, "CUST-EE", "FG-DT100", 8, "EA", 48000, "EGP", "2026-07-11", "2026-08-15", "confirmed", "WH-FG"],
            ["SO-2026-0291", 10, "CUST-DW", "FG-DT100", 4, "EA", 52000, "AED", "2026-07-12", "2026-08-20", "draft", "WH-FG"],
        ],
        "file_type": "sales_orders",
        "phase": 4,
    },
    "purchase_orders_upload_template.xlsx": {
        "sheet": "purchase_orders",
        "headers": [
            "po_number",
            "supplier_code",
            "product_code",
            "quantity",
            "unit_price",
            "currency",
            "expected_delivery",
            "warehouse",
            "status",
        ],
        "hints": {"quantity": "Numeric >= 0"},
        "rows": [
            ["PO-1001", "SUP-CC", "RM-CW25", 200, 21.5, "USD", "2026-07-30", "WH-RM", "confirmed"],
            ["PO-1002", "SUP-NW", "RM-CW25", 80, 22.0, "USD", "2026-07-28", "WH-RM", "confirmed"],
            ["PO-1003", "SUP-SS", "SF-CORE100", 15, 1200, "EGP", "2026-08-05", "WH-WIP", "draft"],
        ],
        "file_type": "purchase_orders",
        "phase": 4,
    },
    "historical_otd_upload_template.xlsx": {
        "sheet": "historical_otd",
        "headers": ["mo_number", "product_code", "customer_code", "planned_end", "actual_end", "delay_days"],
        "hints": {"planned_end": "YYYY-MM-DD", "actual_end": "YYYY-MM-DD"},
        "rows": [
            ["MO-ST-008", "FG-DT100", "CUST-EE", "2026-06-15", "2026-06-18", 3],
            ["MO-ST-009", "FG-DT250", "CUST-SEC", "2026-06-20", "2026-06-20", 0],
            ["MO-ST-010", "FG-DT100", "CUST-DW", "2026-06-25", "2026-06-29", 4],
        ],
        "file_type": "historical_otd",
        "phase": 5,
    },
    "demand_forecast_upload_template.xlsx": {
        "sheet": "demand_forecast",
        "headers": ["product_code", "period", "forecast_qty", "uom", "source", "confidence_pct"],
        "hints": {
            "period": "YYYY-MM or week label",
            "forecast_qty": "Numeric >= 0",
            "source": "statistical|sales|marketing",
        },
        "rows": [
            ["FG-DT100", "2026-08", 24, "EA", "statistical", 78],
            ["FG-DT100", "2026-09", 28, "EA", "sales", 85],
            ["FG-DT250", "2026-08", 15, "EA", "statistical", 72],
        ],
        "file_type": "demand_forecast",
        "phase": 8,
    },
    "quality_results_upload_template.xlsx": {
        "sheet": "quality_results",
        "headers": [
            "mo_number",
            "product_code",
            "inspection_date",
            "result",
            "measured_value",
            "defect_type",
            "inspector",
            "notes",
        ],
        "hints": {
            "result": "pass|fail|on_hold",
            "inspection_date": "YYYY-MM-DD",
            "measured_value": "Numeric",
        },
        "rows": [
            ["MO-ST-008", "FG-DT100", "2026-07-15", "fail", 0.15, "winding_tension", "QC-01", "Rework winding"],
            ["MO-ST-009", "FG-DT250", "2026-07-15", "pass", 0.98, "", "QC-02", ""],
            ["MO-ST-001", "FG-DT100", "2026-07-16", "pass", 0.99, "", "QC-01", ""],
        ],
        "file_type": "quality_results",
        "phase": 8,
    },
    "sop_sales_input_upload_template.xlsx": {
        "sheet": "sop_sales_input",
        "headers": ["product_family", "period", "sales_forecast_qty", "rationale", "region", "confidence_pct"],
        "hints": {
            "product_family": "e.g. DT100, DT250",
            "period": "YYYY-MM",
            "sales_forecast_qty": "Numeric >= 0",
        },
        "rows": [
            ["DT100", "2026-08", 28, "Egyptian Electric expansion", "EG", 80],
            ["DT250", "2026-08", 18, "Saudi program", "SA", 75],
            ["PT500", "2026-08", 6, "Tender pipeline", "AE", 55],
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
        "This pack matches upload-svc **Phases 1–5 + Phase 8** types with **full operational columns**",
        "(e.g. product: code, group, type, short/full name, UoM, main storage location + optional cost/stock fields).",
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
