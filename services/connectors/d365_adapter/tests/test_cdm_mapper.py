"""D365 Adapter CDM Mapper — Integration Tests."""
from __future__ import annotations

from connectors.d365_adapter.cdm_mapper import (
    map_sales_order_to_demand,
    map_purchase_order_to_supply,
    map_production_order_to_manufacturing_order,
    map_product_to_cdm,
)


class TestD365SalesOrderMapping:
    def test_map_basic_sales_order(self):
        d365_order = {
            "SalesOrderNumber": "SO-D365-001",
            "InvoiceCustomerAccountNumber": "CUST-D365-001",
            "ItemNumber": "ITEM-001",
            "OrderedSalesQuantity": 75.0,
            "RequestedShipDate": "2026-07-15",
            "SalesPrice": 120.00,
            "CurrencyCode": "USD",
        }
        result = map_sales_order_to_demand(d365_order)
        assert result["order_id"] == "SO-D365-001"
        assert result["customer_id"] == "CUST-D365-001"
        assert result["product_id"] == "ITEM-001"
        assert result["quantity"] == 75.0
        assert result["due_date"] == "2026-07-15"

    def test_map_sales_order_empty(self):
        d365_order = {"SalesOrderNumber": "SO-D365-002"}
        result = map_sales_order_to_demand(d365_order)
        assert result["order_id"] == "SO-D365-002"
        assert result["quantity"] == 0

    def test_map_sales_order_negative_price(self):
        d365_order = {
            "SalesOrderNumber": "SO-D365-003",
            "SalesPrice": -50.00,
            "OrderedSalesQuantity": 10.0,
        }
        result = map_sales_order_to_demand(d365_order)
        assert result["revenue"] == -50.00


class TestD365PurchaseOrderMapping:
    def test_map_basic_purchase_order(self):
        d365_po = {
            "PurchaseOrderNumber": "PO-D365-001",
            "VendorAccountNumber": "SUPP-D365-001",
            "ItemNumber": "ITEM-001",
            "OrderedPurchaseQuantity": 150.0,
            "RequestedDeliveryDate": "2026-06-20",
            "PurchasePrice": 35.00,
        }
        result = map_purchase_order_to_supply(d365_po)
        assert result["order_id"] == "PO-D365-001"
        assert result["supplier_id"] == "SUPP-D365-001"
        assert result["product_id"] == "ITEM-001"
        assert result["quantity"] == 150.0

    def test_map_purchase_order_missing_fields(self):
        d365_po = {"PurchaseOrderNumber": "PO-D365-002"}
        result = map_purchase_order_to_supply(d365_po)
        assert result["order_id"] == "PO-D365-002"
        assert result["quantity"] == 0


class TestD365ProductionOrderMapping:
    def test_map_basic_production_order(self):
        d365_prod = {
            "ProductionOrderNumber": "MO-D365-001",
            "ItemNumber": "ITEM-001",
            "ProductionQuantity": 200.0,
            "ScheduledStartDate": "2026-06-01",
            "ScheduledEndDate": "2026-06-15",
            "RouteId": "ROUTE-D365-001",
        }
        result = map_production_order_to_manufacturing_order(d365_prod)
        assert result["mo_id"] == "MO-D365-001"
        assert result["product_id"] == "ITEM-001"
        assert result["planned_quantity"] == 200.0
        assert result["planned_start"] == "2026-06-01"
        assert result["planned_end"] == "2026-06-15"

    def test_map_production_order_estimated(self):
        d365_prod = {
            "ProductionOrderNumber": "MO-D365-002",
            "ProductionStatus": "Estimated",
            "ProductionQuantity": 50.0,
        }
        result = map_production_order_to_manufacturing_order(d365_prod)
        assert result["mo_id"] == "MO-D365-002"
        assert result["status"] == "estimated"


class TestD365ProductMapping:
    def test_map_basic_product(self):
        d365_product = {
            "ItemId": "ITEM-001",
            "ProductName": "Assembly X",
            "ProductType": "Item",
            "UnitOfMeasure": "ea",
            "DefaultWarehouse": "WH-MAIN",
        }
        result = map_product_to_cdm(d365_product)
        assert result["product_id"] == "ITEM-001"
        assert result["name"] == "Assembly X"
        assert result["unit"] == "ea"

    def test_map_product_minimal(self):
        d365_product = {"ItemId": "ITEM-002"}
        result = map_product_to_cdm(d365_product)
        assert result["product_id"] == "ITEM-002"
        assert result["name"] == ""
