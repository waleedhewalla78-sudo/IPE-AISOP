"""Unit tests for OdooAdapter transforms (mock API responses)."""

from app.erp.odoo_adapter import OdooAdapter


def test_transform_products():
    adapter = OdooAdapter()
    raw = [{
        "id": 1,
        "name": "Transformer 500 kVA",
        "default_code": "TR-500",
        "categ_id": [5, "Transformers"],
        "type": "product",
        "uom_id": [1, "Units"],
        "tracking": "none",
        "standard_price": 12000,
        "list_price": 15000,
        "qty_available": 3,
    }]
    out = adapter._transform_products(raw)
    assert out[0]["external_id"] == "odoo_product_1"
    assert out[0]["sku"] == "TR-500"
    assert out[0]["qty_available"] == 3


def test_transform_stock():
    adapter = OdooAdapter()
    raw = [{"id": 10, "product_id": [1, "TR-500"], "location_id": [8, "WH/Stock"], "quantity": 100, "reserved_quantity": 20}]
    out = adapter._transform_stock(raw)
    assert out[0]["available"] == 80


def test_transform_boms_with_lines():
    adapter = OdooAdapter()
    raw = [{
        "id": 2,
        "product_id": [1, "TR-500"],
        "product_qty": 1,
        "type": "normal",
        "bom_line_ids": [{"id": 1, "product_id": [3, "Copper"], "product_qty": 50}],
        "operation_ids": [{"id": 1, "name": "Wind", "sequence": 10}],
    }]
    out = adapter._transform_boms(raw)
    assert len(out[0]["components"]) == 1
    assert out[0]["components"][0]["quantity"] == 50


def test_transform_production_odoo19_dates():
    adapter = OdooAdapter()
    raw = [{
        "id": 100,
        "name": "MO/00100",
        "product_id": [1, "TR-500"],
        "product_qty": 2,
        "state": "confirmed",
        "date_start": "2026-07-01 06:00:00",
        "date_finished": "2026-07-05 18:00:00",
        "bom_id": [2, "BOM-TR"],
    }]
    out = adapter._transform_production(raw)
    assert out[0]["scheduled_start"] == "2026-07-01 06:00:00"
    assert out[0]["external_id"] == "odoo_mo_100"


def test_transform_sales_with_lines():
    adapter = OdooAdapter()
    raw = [{
        "id": 5,
        "name": "SO001",
        "partner_id": [7, "Great Lakes Utility"],
        "date_order": "2026-06-01",
        "state": "sale",
        "amount_total": 50000,
        "order_line": [{"id": 1, "product_id": [1, "TR-500"], "product_uom_qty": 2, "price_unit": 25000}],
    }]
    out = adapter._transform_sales(raw)
    assert out[0]["customer"] == "Great Lakes Utility"
    assert len(out[0]["lines"]) == 1


def test_m2o_helper():
    adapter = OdooAdapter()
    assert adapter._m2o([1, "Name"]) == (1, "Name")
    assert adapter._m2o(False) == (False, "")
