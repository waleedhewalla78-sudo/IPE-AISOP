"""Project plan Excel schema definition.

See docs/PROJECT-PLAN-EXCEL-SCHEMA.md for the full user-facing specification.

Sheet name: ProjectPlan (first sheet is used if name differs)
Row 1: column headers (case-insensitive match)
Row 2+: operation rows

Required columns:
  PLAN_CODE          str   Unique plan identifier (same value on every row in a file)
  PLAN_NAME          str   Display name for the plan
  MO_ID              str   Manufacturing order reference (e.g. MO-DEMO-001)
  OPERATION_SEQUENCE int   Operation sequence within the MO (10, 20, 30...)
  OPERATION_NAME     str   Operation description
  WORK_CENTER_CODE   str   Work center ERP id (WC001, WC002, WC003)
  START_HOUR         float Hours from horizon start (0 = beginning of schedule)
  DURATION_HOURS     float Duration in hours (must be > 0)

Optional columns:
  STATUS             str   planned | frozen | disrupted | ai_suggested (default: planned)
  NOTES              str   Free text

To change the schema in future releases, update COLUMN_SPECS below and bump SCHEMA_VERSION.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "1.0"
MAX_FILE_BYTES = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".xlsx"}
ALLOWED_STATUSES = frozenset({"planned", "frozen", "disrupted", "ai_suggested"})


@dataclass(frozen=True)
class ColumnSpec:
    name: str
    required: bool
    data_type: str
    description: str


COLUMN_SPECS: tuple[ColumnSpec, ...] = (
    ColumnSpec("PLAN_CODE", True, "string", "Unique plan code, identical on all rows"),
    ColumnSpec("PLAN_NAME", True, "string", "Human-readable plan title"),
    ColumnSpec("MO_ID", True, "string", "Manufacturing order id (erp_mo_id)"),
    ColumnSpec("OPERATION_SEQUENCE", True, "integer", "Routing sequence number within MO"),
    ColumnSpec("OPERATION_NAME", True, "string", "Operation label shown on Gantt"),
    ColumnSpec("WORK_CENTER_CODE", True, "string", "Work center code (WC001...)"),
    ColumnSpec("START_HOUR", True, "number", "Start offset in hours from horizon 0"),
    ColumnSpec("DURATION_HOURS", True, "number", "Operation duration in hours"),
    ColumnSpec("STATUS", False, "string", "planned|frozen|disrupted|ai_suggested"),
    ColumnSpec("NOTES", False, "string", "Optional planner notes"),
)

REQUIRED_HEADERS = [c.name for c in COLUMN_SPECS if c.required]
OPTIONAL_HEADERS = [c.name for c in COLUMN_SPECS if not c.required]
ALL_HEADERS = [c.name for c in COLUMN_SPECS]

HEADER_ALIASES: dict[str, str] = {
    "PLAN CODE": "PLAN_CODE",
    "PLAN NAME": "PLAN_NAME",
    "MO ID": "MO_ID",
    "MO": "MO_ID",
    "SEQUENCE": "OPERATION_SEQUENCE",
    "OPERATION SEQ": "OPERATION_SEQUENCE",
    "OPERATION": "OPERATION_NAME",
    "WORK CENTER": "WORK_CENTER_CODE",
    "WC": "WORK_CENTER_CODE",
    "START": "START_HOUR",
    "DURATION": "DURATION_HOURS",
}


def normalize_header(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value).strip().upper().replace("-", "_").replace(" ", "_")
    if raw in ALL_HEADERS:
        return raw
    spaced = str(value).strip().upper()
    return HEADER_ALIASES.get(spaced)


def schema_documentation() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "sheet_name": "ProjectPlan",
        "max_file_bytes": MAX_FILE_BYTES,
        "columns": [
            {
                "name": c.name,
                "required": c.required,
                "type": c.data_type,
                "description": c.description,
            }
            for c in COLUMN_SPECS
        ],
    }
