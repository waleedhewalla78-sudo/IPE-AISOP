#!/usr/bin/env python3
"""Generate a sample ProjectPlan Excel template for demos."""

from pathlib import Path

from openpyxl import Workbook

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "templates" / "project-plan-demo-template.xlsx"

ROWS = [
    [
        "PLAN_CODE",
        "PLAN_NAME",
        "MO_ID",
        "OPERATION_SEQUENCE",
        "OPERATION_NAME",
        "WORK_CENTER_CODE",
        "START_HOUR",
        "DURATION_HOURS",
        "STATUS",
        "NOTES",
    ],
    ["PLAN-DEMO-Q3", "Q3 Demo Production Plan", "MO-DEMO-001", 10, "Machine Widget Housing", "WC002", 0, 1.5, "planned", "Op 10"],
    ["PLAN-DEMO-Q3", "Q3 Demo Production Plan", "MO-DEMO-001", 20, "Assemble Widget A", "WC001", 1.5, 2, "planned", "Op 20"],
    ["PLAN-DEMO-Q3", "Q3 Demo Production Plan", "MO-DEMO-001", 30, "Pack Widget A", "WC003", 3.5, 0.75, "planned", "Op 30"],
    ["PLAN-DEMO-Q3", "Q3 Demo Production Plan", "MO-DEMO-005", 10, "Fabricate Gadget B", "WC002", 2.5, 2.5, "frozen", "Frozen op"],
    ["PLAN-DEMO-Q3", "Q3 Demo Production Plan", "MO-DEMO-005", 20, "QC Gadget B", "WC003", 5, 1, "planned", "QC"],
]


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "ProjectPlan"
    for row in ROWS:
        ws.append(row)
    wb.save(OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
