"""Purchase Order suggestion engine.

When material netting detects shortages, this module generates PO suggestions
with optimal order quantities based on safety stock levels, economic order
quantities, and supplier constraints.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any


def calculate_eoq(
    annual_demand: float,
    order_cost: float,
    holding_cost_per_unit: float,
) -> float:
    """Calculate Economic Order Quantity.

    EOQ = sqrt(2 * D * S / H)
    Where:
        D = annual demand
        S = ordering cost per order
        H = holding cost per unit per year
    """
    if holding_cost_per_unit <= 0 or annual_demand <= 0:
        return 0.0
    return math.sqrt(2 * annual_demand * order_cost / holding_cost_per_unit)


def suggest_order_quantity(
    shortage_qty: float,
    safety_stock_qty: float,
    avg_daily_demand: float,
    lead_time_days: float,
    eoq: float = 0,
    min_order_qty: float = 1,
    max_order_qty: float | None = None,
    order_multiple: float = 1,
) -> float:
    """Determine optimal order quantity.

    Strategy: max(shortage + safety_stock, EOQ, min_order_qty)
    Rounded up to order_multiple.
    """
    base_qty = shortage_qty + safety_stock_qty

    if eoq > 0:
        base_qty = max(base_qty, eoq)

    base_qty = max(base_qty, min_order_qty)

    if max_order_qty is not None:
        base_qty = min(base_qty, max_order_qty)

    if order_multiple > 1:
        base_qty = math.ceil(base_qty / order_multiple) * order_multiple

    return round(base_qty, 2)


def generate_po_suggestions(
    shortages: list[dict],
    suppliers: dict[str, dict],
    service_level: float = 0.95,
    holding_cost_pct: float = 0.25,
    order_cost: float = 50.0,
) -> list[dict[str, Any]]:
    """Generate PO suggestions from shortage data.

    Args:
        shortages: List of dicts with:
            - product_id: str
            - component_name: str
            - shortage_qty: float
            - avg_daily_demand: float
            - demand_std_dev: float (optional)
            - required_date: str (ISO date)
        suppliers: Dict mapping product_id -> supplier info:
            - supplier_id: str
            - supplier_name: str
            - lead_time_days: float
            - lead_time_std_dev: float
            - unit_cost: float
            - min_order_qty: float (optional)
            - order_multiple: float (optional)
        service_level: Target service level.
        holding_cost_pct: Annual holding cost as % of unit cost.
        order_cost: Fixed cost per purchase order.

    Returns:
        List of PO suggestion dicts.
    """
    from app.core.safety_stock import calculate_safety_stock

    suggestions = []

    for shortage in shortages:
        product_id = shortage.get("product_id", "")
        supplier_info = suppliers.get(product_id, {})

        avg_daily = float(shortage.get("avg_daily_demand", 0))
        demand_std = float(shortage.get("demand_std_dev", 0))
        shortage_qty = float(shortage.get("shortage_qty", 0))
        required_date = shortage.get("required_date", "")

        lt_days = float(supplier_info.get("lead_time_days", 7))
        lt_std = float(supplier_info.get("lead_time_std_dev", 1))
        unit_cost = float(supplier_info.get("unit_cost", 0))
        min_order = float(supplier_info.get("min_order_qty", 1))
        order_multiple = float(supplier_info.get("order_multiple", 1))

        ss_calc = calculate_safety_stock(
            avg_daily_demand=avg_daily,
            demand_std_dev=demand_std,
            avg_lead_time_days=lt_days,
            lead_time_std_dev=lt_std,
            service_level=service_level,
        )
        safety_stock = ss_calc["safety_stock_qty"]

        annual_demand = avg_daily * 365
        holding_cost = unit_cost * holding_cost_pct
        eoq = calculate_eoq(annual_demand, order_cost, holding_cost)

        order_qty = suggest_order_quantity(
            shortage_qty=shortage_qty,
            safety_stock_qty=safety_stock,
            avg_daily_demand=avg_daily,
            lead_time_days=lt_days,
            eoq=eoq,
            min_order_qty=min_order,
            order_multiple=order_multiple,
        )

        if required_date:
            try:
                req_dt = datetime.fromisoformat(required_date)
            except (ValueError, TypeError):
                req_dt = datetime.utcnow()
        else:
            req_dt = datetime.utcnow()

        order_date = req_dt - timedelta(days=lt_days)
        expected_delivery = req_dt

        total_cost = order_qty * unit_cost

        suggestions.append({
            "product_id": product_id,
            "component_name": shortage.get("component_name", ""),
            "supplier_id": supplier_info.get("supplier_id", ""),
            "supplier_name": supplier_info.get("supplier_name", ""),
            "order_quantity": order_qty,
            "unit_cost": unit_cost,
            "total_cost": round(total_cost, 2),
            "safety_stock_qty": safety_stock,
            "eoq": round(eoq, 2),
            "suggested_order_date": order_date.strftime("%Y-%m-%d") if isinstance(order_date, datetime) else str(order_date),
            "expected_delivery_date": expected_delivery.strftime("%Y-%m-%d") if isinstance(expected_delivery, datetime) else str(expected_delivery),
            "lead_time_days": lt_days,
            "shortage_qty": shortage_qty,
            "service_level": service_level,
            "priority": "urgent" if shortage_qty > safety_stock * 2 else "normal",
        })

    suggestions.sort(key=lambda s: (
        0 if s["priority"] == "urgent" else 1,
        s.get("expected_delivery_date", ""),
    ))

    return suggestions


def merge_po_suggestions(suggestions: list[dict]) -> list[dict]:
    """Merge PO suggestions for same product+supplier into single orders.

    Combines quantities and takes the latest required date.
    """
    merged: dict[str, dict] = {}

    for s in suggestions:
        key = f"{s['product_id']}_{s['supplier_id']}"
        if key not in merged:
            merged[key] = {**s}
        else:
            existing = merged[key]
            existing["order_quantity"] = round(
                existing["order_quantity"] + s["order_quantity"], 2
            )
            existing["total_cost"] = round(
                existing["total_cost"] + s["total_cost"], 2
            )
            existing["shortage_qty"] = round(
                existing["shortage_qty"] + s["shortage_qty"], 2
            )
            if s.get("expected_delivery_date", "") > existing.get("expected_delivery_date", ""):
                existing["expected_delivery_date"] = s["expected_delivery_date"]
            if s.get("suggested_order_date", "") < existing.get("suggested_order_date", ""):
                existing["suggested_order_date"] = s["suggested_order_date"]
            existing["priority"] = (
                "urgent" if existing["shortage_qty"] > existing.get("safety_stock_qty", 0) * 2
                else existing["priority"]
            )

    return list(merged.values())
