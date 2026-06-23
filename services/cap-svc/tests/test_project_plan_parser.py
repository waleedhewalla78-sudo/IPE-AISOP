"""Unit tests for project plan Excel parsing."""

import io

import pytest
from openpyxl import Workbook

from app.core.project_plan_parser import ProjectPlanParseError, parse_project_plan_excel


def _build_workbook(rows: list[list], sheet_name: str = "ProjectPlan") -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


HEADER = [
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
]

VALID_ROW = [
    "PLAN-DEMO-Q3",
    "Q3 Demo Production",
    "MO-DEMO-001",
    10,
    "Assemble Widget A",
    "WC001",
    1.5,
    2,
    "planned",
    "Demo row",
]


def test_parse_valid_workbook():
    row2 = VALID_ROW.copy()
    row2[3] = 20
    row2[8] = "frozen"
    row2[9] = ""
    content = _build_workbook([HEADER, VALID_ROW, row2])
    parsed = parse_project_plan_excel("plan.xlsx", content)
    assert parsed["plan_code"] == "PLAN-DEMO-Q3"
    assert parsed["row_count"] == 2
    assert parsed["operations"][0]["start_minute"] == 90.0


def test_rejects_non_xlsx_extension():
    content = _build_workbook([HEADER, VALID_ROW])
    with pytest.raises(ProjectPlanParseError, match="Invalid file type"):
        parse_project_plan_excel("plan.csv", content)


def test_rejects_missing_required_column():
    bad_header = HEADER.copy()
    bad_header.remove("MO_ID")
    content = _build_workbook([bad_header, VALID_ROW[:8]])
    with pytest.raises(ProjectPlanParseError, match="Missing column: MO_ID"):
        parse_project_plan_excel("plan.xlsx", content)


def test_rejects_duplicate_mo_sequence():
    content = _build_workbook([HEADER, VALID_ROW, VALID_ROW])
    with pytest.raises(ProjectPlanParseError, match="duplicate"):
        parse_project_plan_excel("plan.xlsx", content)


def test_rejects_multiple_plan_codes():
    row2 = VALID_ROW.copy()
    row2[0] = "OTHER-PLAN"
    row2[3] = 20
    content = _build_workbook([HEADER, VALID_ROW, row2])
    with pytest.raises(ProjectPlanParseError, match="Found multiple plan codes"):
        parse_project_plan_excel("plan.xlsx", content)


def test_rejects_invalid_status():
    row = VALID_ROW.copy()
    row[8] = "invalid"
    content = _build_workbook([HEADER, row])
    with pytest.raises(ProjectPlanParseError, match="STATUS must be one of"):
        parse_project_plan_excel("plan.xlsx", content)


def test_rejects_oversized_file():
    content = _build_workbook([HEADER, VALID_ROW])
    oversized = content + (b"0" * (6 * 1024 * 1024))
    with pytest.raises(ProjectPlanParseError, match="maximum size"):
        parse_project_plan_excel("plan.xlsx", oversized)


def test_rejects_empty_file():
    with pytest.raises(ProjectPlanParseError, match="empty"):
        parse_project_plan_excel("plan.xlsx", b"")
