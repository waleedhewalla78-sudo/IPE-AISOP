from __future__ import annotations


def rollup_costs(qty: float | int | None, price: float | int | None, unit_cost: float | int | None) -> dict:
    quantity = float(qty or 0)
    unit_price = float(price or 0)
    cost_each = float(unit_cost or 0)
    revenue = quantity * unit_price
    cost = quantity * cost_each
    return {
        "revenue": revenue,
        "cost": cost,
        "profit": revenue - cost,
    }
