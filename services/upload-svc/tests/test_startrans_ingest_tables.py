"""SHEET_TABLE points at canonical ingest tables, not demo_*."""

from app.core.startrans_ingest import SHEET_TABLE
from app.core.startrans_workbook import EXPECTED_SHEETS, NATURAL_KEYS, compose_natural_key

DATA_SHEETS = [s for s in EXPECTED_SHEETS if s != "README"]


def test_sheet_table_uses_cdm_ingest():
    assert all(v.startswith("cdm_ingest_") for v in SHEET_TABLE.values())
    assert "demo_" not in ",".join(SHEET_TABLE.values())
    assert SHEET_TABLE["04_Products"] == "cdm_ingest_product"
    assert SHEET_TABLE["12_ManufacturingOrders"] == "cdm_ingest_manufacturing_order"


def test_all_data_sheets_mapped():
    for sheet in DATA_SHEETS:
        assert sheet in SHEET_TABLE, f"unmapped data sheet: {sheet}"
        assert sheet in NATURAL_KEYS, f"missing natural key: {sheet}"
    assert "README" not in SHEET_TABLE


def test_missed_sheet_tables():
    assert SHEET_TABLE["03b_CalendarShifts"] == "cdm_ingest_calendar_shift"
    assert SHEET_TABLE["03c_CalendarExceptions"] == "cdm_ingest_calendar_exception"
    assert SHEET_TABLE["06b_BOMLines"] == "cdm_ingest_bom_component"
    assert SHEET_TABLE["07b_RoutingOperations"] == "cdm_ingest_routing_operation"
    assert SHEET_TABLE["10a_Employees"] == "cdm_ingest_employee"
    assert SHEET_TABLE["10b_EmployeeSkills"] == "cdm_ingest_employee_skill"
    assert SHEET_TABLE["11b_SalesOrderLines"] == "cdm_ingest_sales_order_line"
    assert SHEET_TABLE["13b_PurchaseOrderLines"] == "cdm_ingest_purchase_order_line"
    assert SHEET_TABLE["16_ExecutionEvents"] == "cdm_ingest_execution_event"


def test_composite_natural_keys():
    shift = compose_natural_key(
        "03b_CalendarShifts",
        {"calendar_id": "CAL-A", "day_of_week": 0, "shift_number": 1},
    )
    assert shift == "CAL-A:0:1"
    line = compose_natural_key(
        "06b_BOMLines",
        {"bom_id": "BOM-1", "line_number": 10, "material_id": "MAT-1"},
    )
    assert line == "BOM-1:10"
    skill = compose_natural_key(
        "10b_EmployeeSkills",
        {"employee_id": "EMP-1", "skill_code": "SKILL-A"},
    )
    assert skill == "EMP-1:SKILL-A"
    event = compose_natural_key(
        "16_ExecutionEvents",
        {
            "event_type": "operation_start",
            "event_datetime": "2026-08-13T08:15:00",
            "mo_id": "MO-ST-007",
            "operation_id": "OP-020",
        },
    )
    assert event.startswith("operation_start:2026-08-13T08:15:00:MO-ST-007:")
