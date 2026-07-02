"""Multi-echelon supply network planning helpers."""

from __future__ import annotations


def build_replenishment_plan(
    plants: list[dict],
    routes: list[dict],
    inventory_rows: list[dict],
) -> dict:
    nodes = [
        {
            "plant_id": str(p["id"]),
            "name": p.get("name") or p.get("code"),
            "on_hand_units": sum(
                float(r.get("qty_on_hand", 0))
                for r in inventory_rows
                if str(r.get("location_id", "")) == str(p.get("id"))
            ),
        }
        for p in plants
    ]
    lanes = [
        {
            "from": str(r["origin_plant_id"]),
            "to": str(r["destination_plant_id"]),
            "lead_time_hours": float(r.get("transit_time_hours", 24)),
            "cost_per_unit": float(r.get("cost_per_unit", 0)),
        }
        for r in routes
    ]
    total_on_hand = sum(n["on_hand_units"] for n in nodes)
    transfers = []
    if len(nodes) >= 2 and total_on_hand > 0:
        donor, receiver = sorted(nodes, key=lambda n: n["on_hand_units"], reverse=True)[0], sorted(
            nodes, key=lambda n: n["on_hand_units"]
        )[0]
        qty = round(min(donor["on_hand_units"] * 0.15, 500), 2)
        if qty > 0:
            transfers.append(
                {
                    "from_plant": donor["plant_id"],
                    "to_plant": receiver["plant_id"],
                    "quantity": qty,
                    "reason": "rebalance_safety_stock",
                }
            )
    return {
        "nodes": nodes,
        "lanes": lanes,
        "recommended_transfers": transfers,
        "network_inventory_total": round(total_on_hand, 2),
        "echelon_count": len(nodes),
    }
