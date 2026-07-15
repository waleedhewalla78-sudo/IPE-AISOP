"""A1.5 Order promising — ATP / CTP / Profitable-to-Promise (PTP)."""

from __future__ import annotations

from typing import Any


def promise_order(
    *,
    order_id: str,
    product_id: str,
    qty: float,
    requested_date: str,
    inventory_available: float,
    capacity_available_hrs: float,
    hours_per_unit: float = 2.5,
    unit_cost: float = 8500.0,
    unit_price: float = 12_000.0,
    material_lead_days: int = 0,
    reserved_inventory: float = 0.0,
    production_lead_days: int = 7,
    opportunity_cost: float = 0.0,
) -> dict[str, Any]:
    """Return can-promise answer with ATP/CTP breakdown, confidence, and PTP."""
    atp_qty = max(0.0, float(inventory_available) - float(reserved_inventory))
    from_stock = min(qty, atp_qty)
    from_production = max(0.0, qty - from_stock)

    material_ok = from_production == 0 or material_lead_days <= 10
    hours_needed = from_production * hours_per_unit
    capacity_ok = capacity_available_hrs >= hours_needed

    if from_stock >= qty:
        status = "accept"
        promised = requested_date
        confidence = 0.95
        delay_days = 0
        bottleneck = None
        level = "ATP"
    elif capacity_ok and material_ok:
        status = "accept"
        delay_days = 0
        promised = requested_date
        confidence = 0.9
        bottleneck = None
        level = "CTP"
    elif capacity_ok and not material_ok:
        status = "accept_with_delay"
        delay_days = max(material_lead_days, 5)
        promised = requested_date
        confidence = 0.75
        bottleneck = "material"
        level = "CTP"
    elif material_ok and not capacity_ok:
        status = "accept_with_delay"
        overload = hours_needed - capacity_available_hrs
        delay_days = max(1, int((overload / max(capacity_available_hrs, 1)) * 7))
        promised = requested_date
        confidence = 0.7
        bottleneck = "capacity"
        level = "CTP"
    else:
        status = "negotiate"
        delay_days = max(material_lead_days, production_lead_days, 10)
        promised = requested_date
        confidence = 0.45
        bottleneck = "material+capacity"
        level = "CTP"

    revenue = qty * unit_price
    cost = qty * unit_cost
    margin = revenue - cost
    margin_pct = round((margin / revenue) * 100, 1) if revenue else 0.0
    net_benefit = margin - opportunity_cost
    ptp_recommendation = "accept" if net_benefit > 0 and status != "negotiate" else "review"

    return {
        "order_id": order_id,
        "product_id": product_id,
        "qty": qty,
        "requested_date": requested_date,
        "status": status,
        "promised_date": promised,
        "delay_days": delay_days,
        "confidence": confidence,
        "bottleneck": bottleneck,
        "promise_level": level,
        "breakdown": {
            "from_stock": from_stock,
            "from_production": from_production,
            "atp_available": atp_qty,
            "production_lead_days": production_lead_days,
        },
        "checks": {
            "material_ok": material_ok,
            "capacity_ok": capacity_ok,
            "hours_needed": round(hours_needed, 1),
            "hours_available": capacity_available_hrs,
            "inventory_available": inventory_available,
        },
        "commercial": {
            "revenue": revenue,
            "cost": cost,
            "margin": margin,
            "margin_pct": margin_pct,
            "opportunity_cost": opportunity_cost,
            "net_benefit": net_benefit,
            "recommendation": (
                "accept" if margin_pct >= 20 and status != "negotiate" else "review"
            ),
        },
        "ptp": {
            "recommendation": ptp_recommendation,
            "net_benefit": net_benefit,
            "margin_pct": margin_pct,
        },
    }
