"""A1.2 Master Production Schedule builder."""

from __future__ import annotations

from typing import Any


def build_mps(
    *,
    product_id: str,
    lot_size: int = 5,
    safety_stock: float = 15,
    opening_inventory: float = 45,
    weeks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compute weekly MPS rows from forecast + firm orders."""
    weeks = weeks or [
        {"week": "W29", "forecast": 25, "orders": 23},
        {"week": "W30", "forecast": 22, "orders": 8},
        {"week": "W31", "forecast": 28, "orders": 3},
        {"week": "W32", "forecast": 25, "orders": 0},
        {"week": "W33", "forecast": 30, "orders": 0},
        {"week": "W34", "forecast": 25, "orders": 0},
    ]
    inv = float(opening_inventory)
    rows: list[dict[str, Any]] = []
    draft_mos: list[dict[str, Any]] = []
    for w in weeks:
        demand = max(float(w.get("forecast", 0)), float(w.get("orders", 0)))
        available = inv
        net = max(0.0, demand - available + safety_stock) if available < demand + safety_stock else 0.0
        # Net requirement after consuming demand from opening inventory
        after_demand = available - demand
        if after_demand >= safety_stock:
            net_req = 0.0
            planned = 0
        else:
            net_req = safety_stock - after_demand if after_demand < safety_stock else 0.0
            if after_demand < 0:
                net_req = -after_demand + safety_stock
            planned = int(((net_req + lot_size - 1) // lot_size) * lot_size) if net_req > 0 else 0
        projected = after_demand + planned
        status = "ok"
        if projected < safety_stock:
            status = "below_ss"
        if projected < 0:
            status = "short"
        row = {
            "week": w.get("week"),
            "forecast_demand": float(w.get("forecast", 0)),
            "customer_orders": float(w.get("orders", 0)),
            "available_inventory": round(available, 1),
            "net_requirement": round(max(0.0, net_req), 1),
            "planned_production": planned,
            "projected_inventory": round(projected, 1),
            "safety_stock_target": safety_stock,
            "status": status,
        }
        rows.append(row)
        if planned > 0:
            draft_mos.append(
                {
                    "product_id": product_id,
                    "week": w.get("week"),
                    "qty": planned,
                    "status": "draft",
                    "reason": "mps_net_requirement",
                }
            )
        inv = projected

    below = [r for r in rows if r["status"] in ("below_ss", "short")]
    recommendation = None
    first_prod = next((r for r in rows if r["planned_production"] > 0), None)
    if first_prod:
        recommendation = (
            f"Start production of {first_prod['planned_production']} units in "
            f"{first_prod['week']}. Auto-drafted MO pending planner approval."
        )

    return {
        "product_id": product_id,
        "lot_size": lot_size,
        "safety_stock": safety_stock,
        "opening_inventory": opening_inventory,
        "weeks": rows,
        "exceptions": below,
        "draft_mos": draft_mos,
        "recommendation": recommendation,
    }
