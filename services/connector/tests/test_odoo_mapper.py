"""Unit tests for Odoo 17 mappers."""

from datetime import UTC, datetime

from app.core.mapper import (
    map_odoo_mo_state,
    map_odoo_to_cdm,
    ODOO_TO_CDM_MO,
    ODOO_TO_CDM_PRODUCT,
    ODOO_TO_CDM_WC,
    parse_odoo_datetime,
)


def test_map_odoo_mo_state_confirmed():
    assert map_odoo_mo_state("confirmed") == "confirmed"


def test_map_odoo_mo_state_progress():
    assert map_odoo_mo_state("progress") == "in_progress"


def test_parse_odoo_datetime_string():
    dt = parse_odoo_datetime("2026-06-15 08:30:00")
    assert dt == datetime(2026, 6, 15, 8, 30, 0, tzinfo=UTC)


def test_map_product_from_odoo_record():
    rec = {
        "id": 42,
        "name": "Transformer 500 kVA",
        "default_code": "TR-500",
        "type": "product",
        "uom_id": [1, "Units"],
        "standard_price": 12000.0,
    }
    mapped = map_odoo_to_cdm(rec, ODOO_TO_CDM_PRODUCT)
    assert mapped["erp_source_id"] == "42"
    assert mapped["name"] == "Transformer 500 kVA"
    assert mapped["source_type"] == "manufactured"


def test_map_work_center_default_capacity():
    rec = {"id": 3, "name": "Winding", "code": "WC01", "time_efficiency": 100}
    mapped = map_odoo_to_cdm(rec, ODOO_TO_CDM_WC)
    assert mapped["name"] == "Winding"


def test_map_mo_from_odoo17_record():
    rec = {
        "id": 1001,
        "name": "WH/MO/01001",
        "product_id": [55, "Transformer"],
        "bom_id": [12, "BOM-TR"],
        "product_qty": 2.0,
        "date_start": "2026-07-01 06:00:00",
        "date_finished": "2026-07-05 18:00:00",
        "state": "confirmed",
        "write_date": "2026-06-29 10:00:00",
    }
    mapped = map_odoo_to_cdm(rec, ODOO_TO_CDM_MO)
    assert mapped["erp_mo_id"] == "1001"
    assert mapped["product_erp_id"] == "55"
    assert mapped["bom_erp_id"] == "12"
    assert mapped["quantity"] == 2.0
    assert mapped["status"] == "confirmed"


def test_map_mo_missing_bom_id():
    rec = {"id": 2, "product_id": [1, "P"], "bom_id": False, "product_qty": 1, "state": "draft"}
    mapped = map_odoo_to_cdm(rec, ODOO_TO_CDM_MO)
    assert mapped.get("bom_erp_id") is None


def test_map_product_type_consu():
    rec = {"id": 1, "name": "Copper", "type": "consu", "uom_id": [1, "kg"]}
    mapped = map_odoo_to_cdm(rec, ODOO_TO_CDM_PRODUCT)
    assert mapped["source_type"] == "purchased"


def test_parse_odoo_datetime_none():
    assert parse_odoo_datetime(None) is None
    assert parse_odoo_datetime(False) is None


def test_map_odoo_mo_state_cancel():
    assert map_odoo_mo_state("cancel") == "cancelled"
