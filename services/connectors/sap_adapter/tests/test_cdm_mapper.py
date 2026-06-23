"""SAP Adapter CDM Mapper — Integration Tests."""
from __future__ import annotations

from connectors.sap_adapter.cdm_mapper import (
    map_sale_order_to_demand,
    map_purchase_order_to_supply,
    map_mrp_production_to_manufacturing_order,
    map_material_to_product,
)


class TestSAPSaleOrderMapping:
    def test_map_basic_sale_order(self):
        sap_order = {
            "VBELN": "SO001",
            "KUNNR": "CUST001",
            "MATNR": "MAT-A001",
            "KWMENG": 100.0,
            "LFDAT": "2026-07-01",
            "NETWR": 25000.00,
            "WAERK": "USD",
        }
        result = map_sale_order_to_demand(sap_order)
        assert result["order_id"] == "SO001"
        assert result["customer_id"] == "CUST001"
        assert result["product_id"] == "MAT-A001"
        assert result["quantity"] == 100.0
        assert result["due_date"] == "2026-07-01"
        assert result["revenue"] == 25000.00

    def test_map_sale_order_empty_fields(self):
        sap_order = {"VBELN": "SO002", "KUNNR": "", "MATNR": "MAT-B001", "KWMENG": 0}
        result = map_sale_order_to_demand(sap_order)
        assert result["order_id"] == "SO002"
        assert result["customer_id"] == ""
        assert result["quantity"] == 0

    def test_map_sale_order_missing_fields(self):
        sap_order = {"VBELN": "SO003"}
        result = map_sale_order_to_demand(sap_order)
        assert result["order_id"] == "SO003"
        assert result["quantity"] == 0
        assert result["due_date"] == ""

    def test_map_sale_order_negative_quantity(self):
        sap_order = {"VBELN": "SO004", "KWMENG": -10.0}
        result = map_sale_order_to_demand(sap_order)
        assert result["quantity"] == -10


class TestSAPPurchaseOrderMapping:
    def test_map_basic_purchase_order(self):
        sap_po = {
            "EBELN": "PO001",
            "LIFNR": "SUPP001",
            "MATNR": "MAT-A001",
            "MENGE": 200.0,
            "LFDAT": "2026-06-15",
            "NETPR": 50.00,
        }
        result = map_purchase_order_to_supply(sap_po)
        assert result["order_id"] == "PO001"
        assert result["supplier_id"] == "SUPP001"
        assert result["product_id"] == "MAT-A001"
        assert result["quantity"] == 200.0
        assert result["expected_date"] == "2026-06-15"

    def test_map_purchase_order_missing_fields(self):
        sap_po = {"EBELN": "PO002"}
        result = map_purchase_order_to_supply(sap_po)
        assert result["order_id"] == "PO002"
        assert result["quantity"] == 0


class TestSAPMRPProductionMapping:
    def test_map_basic_mrp_production(self):
        sap_mrp = {
            "AUFNR": "MO001",
            "MATNR": "MAT-A001",
            "GAMNG": 50.0,
            "GSTRP": "2026-06-01",
            "GLTRP": "2026-06-10",
            "PLNNR": "ROUTE001",
        }
        result = map_mrp_production_to_manufacturing_order(sap_mrp)
        assert result["mo_id"] == "MO001"
        assert result["product_id"] == "MAT-A001"
        assert result["planned_quantity"] == 50.0
        assert result["planned_start"] == "2026-06-01"
        assert result["planned_end"] == "2026-06-10"

    def test_map_mrp_production_missing_route(self):
        sap_mrp = {"AUFNR": "MO002", "MATNR": "MAT-B001", "GAMNG": 10.0}
        result = map_mrp_production_to_manufacturing_order(sap_mrp)
        assert result["mo_id"] == "MO002"
        assert result["route_id"] == ""


class TestSAPMaterialMapping:
    def test_map_basic_material(self):
        sap_mat = {
            "MATNR": "MAT-A001",
            "MAKTX": "Widget A",
            "MTART": "FERT",
            "MEINS": "EA",
            "LGORT": "WH01",
        }
        result = map_material_to_product(sap_mat)
        assert result["product_id"] == "MAT-A001"
        assert result["name"] == "Widget A"
        assert result["type"] == "FERT"
        assert result["unit"] == "EA"

    def test_map_material_raw(self):
        sap_mat = {"MATNR": "RAW-001", "MAKTX": "Steel Sheet", "MTART": "ROH"}
        result = map_material_to_product(sap_mat)
        assert result["product_id"] == "RAW-001"
        assert result["type"] == "ROH"
