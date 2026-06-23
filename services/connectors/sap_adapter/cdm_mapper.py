"""SAP Adapter CDM Mapper.

Maps SAP IDoc/BAPI fields to IPE CDM (Canonical Data Model) format.
"""
from __future__ import annotations

from typing import Any


def map_sale_order_to_demand(sap_order: dict[str, Any]) -> dict[str, Any]:
    """Map SAP SD Sales Order (VA01/VA02) to IPE demand line."""
    return {
        "order_id": sap_order.get("VBELN", ""),
        "customer_id": sap_order.get("KUNNR", ""),
        "product_id": sap_order.get("MATNR", ""),
        "quantity": float(sap_order.get("KWMENG", 0)),
        "due_date": sap_order.get("LFDAT", ""),
        "revenue": float(sap_order.get("NETWR", 0)),
        "currency": sap_order.get("WAERK", "USD"),
        "source": "sap",
    }


def map_purchase_order_to_supply(sap_po: dict[str, Any]) -> dict[str, Any]:
    """Map SAP MM Purchase Order (ME21N/ME22N) to IPE supply order."""
    return {
        "order_id": sap_po.get("EBELN", ""),
        "supplier_id": sap_po.get("LIFNR", ""),
        "product_id": sap_po.get("MATNR", ""),
        "quantity": float(sap_po.get("MENGE", 0)),
        "expected_date": sap_po.get("LFDAT", ""),
        "unit_price": float(sap_po.get("NETPR", 0)),
        "source": "sap",
    }


def map_mrp_production_to_manufacturing_order(sap_mrp: dict[str, Any]) -> dict[str, Any]:
    """Map SAP PP Production Order (CO01/CO02) to IPE manufacturing order."""
    return {
        "mo_id": sap_mrp.get("AUFNR", ""),
        "product_id": sap_mrp.get("MATNR", ""),
        "planned_quantity": float(sap_mrp.get("GAMNG", 0)),
        "planned_start": sap_mrp.get("GSTRP", ""),
        "planned_end": sap_mrp.get("GLTRP", ""),
        "route_id": sap_mrp.get("PLNNR", ""),
        "source": "sap",
    }


def map_material_to_product(sap_mat: dict[str, Any]) -> dict[str, Any]:
    """Map SAP MM Material Master (MM01/MM02) to IPE product."""
    return {
        "product_id": sap_mat.get("MATNR", ""),
        "name": sap_mat.get("MAKTX", ""),
        "type": sap_mat.get("MTART", ""),
        "unit": sap_mat.get("MEINS", ""),
        "warehouse": sap_mat.get("LGORT", ""),
        "source": "sap",
    }
