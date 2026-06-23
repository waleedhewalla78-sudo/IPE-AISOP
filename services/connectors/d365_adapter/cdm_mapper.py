"""D365 Adapter CDM Mapper.

Maps D365 Finance & Operations fields to IPE CDM (Canonical Data Model) format.
"""
from __future__ import annotations

from typing import Any


def map_sales_order_to_demand(d365_order: dict[str, Any]) -> dict[str, Any]:
    """Map D365 Sales Order to IPE demand line."""
    return {
        "order_id": d365_order.get("SalesOrderNumber", ""),
        "customer_id": d365_order.get("InvoiceCustomerAccountNumber", ""),
        "product_id": d365_order.get("ItemNumber", ""),
        "quantity": float(d365_order.get("OrderedSalesQuantity", 0)),
        "due_date": d365_order.get("RequestedShipDate", ""),
        "revenue": float(d365_order.get("SalesPrice", 0)) * float(d365_order.get("OrderedSalesQuantity", 0)),
        "currency": d365_order.get("CurrencyCode", "USD"),
        "source": "d365",
    }


def map_purchase_order_to_supply(d365_po: dict[str, Any]) -> dict[str, Any]:
    """Map D365 Purchase Order to IPE supply order."""
    return {
        "order_id": d365_po.get("PurchaseOrderNumber", ""),
        "supplier_id": d365_po.get("VendorAccountNumber", ""),
        "product_id": d365_po.get("ItemNumber", ""),
        "quantity": float(d365_po.get("OrderedPurchaseQuantity", 0)),
        "expected_date": d365_po.get("RequestedDeliveryDate", ""),
        "unit_price": float(d365_po.get("PurchasePrice", 0)),
        "source": "d365",
    }


def map_production_order_to_manufacturing_order(d365_prod: dict[str, Any]) -> dict[str, Any]:
    """Map D365 Production Order to IPE manufacturing order."""
    return {
        "mo_id": d365_prod.get("ProductionOrderNumber", ""),
        "product_id": d365_prod.get("ItemNumber", ""),
        "planned_quantity": float(d365_prod.get("ProductionQuantity", 0)),
        "planned_start": d365_prod.get("ScheduledStartDate", ""),
        "planned_end": d365_prod.get("ScheduledEndDate", ""),
        "route_id": d365_prod.get("RouteId", ""),
        "status": d365_prod.get("ProductionStatus", "").lower(),
        "source": "d365",
    }


def map_product_to_cdm(d365_product: dict[str, Any]) -> dict[str, Any]:
    """Map D365 Product to IPE product."""
    return {
        "product_id": d365_product.get("ItemId", ""),
        "name": d365_product.get("ProductName", ""),
        "type": d365_product.get("ProductType", ""),
        "unit": d365_product.get("UnitOfMeasure", ""),
        "warehouse": d365_product.get("DefaultWarehouse", ""),
        "source": "d365",
    }
