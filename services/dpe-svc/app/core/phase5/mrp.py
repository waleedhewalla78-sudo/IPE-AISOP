"""A1.3 MRP multi-level explosion with PO action flags."""

from __future__ import annotations

from typing import Any


def explode_mrp(
    *,
    product_id: str,
    mo_qty: float,
    bom: list[dict[str, Any]] | None = None,
    inventory: dict[str, dict[str, float]] | None = None,
    scrap_pct: float = 0.0,
) -> dict[str, Any]:
    """
    Explode MPS/MO demand through BOM.

    bom item: material_id, qty_per, level, lead_days, supplier, parent (optional)
    inventory: material_id -> {on_hand, in_transit, reserved, safety_stock}
    """
    bom = bom or [
        {"material_id": "SA-CAL", "qty_per": 1, "level": 1, "lead_days": 0, "supplier": "internal"},
        {"material_id": "RM-SSL", "qty_per": 20, "level": 2, "lead_days": 21, "supplier": "Shanghai Silicon", "parent": "SA-CAL"},
        {"material_id": "RM-INS", "qty_per": 3, "level": 2, "lead_days": 5, "supplier": "Local Insul", "parent": "SA-CAL"},
        {"material_id": "SA-HVW", "qty_per": 1, "level": 1, "lead_days": 0, "supplier": "internal"},
        {"material_id": "RM-CW25", "qty_per": 10, "level": 2, "lead_days": 8, "supplier": "Cairo Copper", "parent": "SA-HVW"},
        {"material_id": "RM-CW40", "qty_per": 8, "level": 2, "lead_days": 8, "supplier": "Cairo Copper", "parent": "SA-HVW"},
    ]
    inventory = inventory or {
        "SA-CAL": {"on_hand": 0, "in_transit": 0, "reserved": 0, "safety_stock": 0},
        "RM-SSL": {"on_hand": 280, "in_transit": 200, "reserved": 0, "safety_stock": 50},
        "RM-INS": {"on_hand": 45, "in_transit": 0, "reserved": 0, "safety_stock": 10},
        "SA-HVW": {"on_hand": 0, "in_transit": 0, "reserved": 0, "safety_stock": 0},
        "RM-CW25": {"on_hand": 450, "in_transit": 0, "reserved": 320, "safety_stock": 40},
        "RM-CW40": {"on_hand": 380, "in_transit": 0, "reserved": 150, "safety_stock": 40},
    }

    lines: list[dict[str, Any]] = []
    po_needed: list[dict[str, Any]] = []
    sufficient = 0
    total_purchased = 0

    for item in sorted(bom, key=lambda x: int(x.get("level", 1))):
        mid = str(item["material_id"])
        gross = mo_qty * float(item.get("qty_per", 1)) * (1 + scrap_pct)
        inv = inventory.get(mid, {"on_hand": 0, "in_transit": 0, "reserved": 0, "safety_stock": 0})
        available = (
            float(inv.get("on_hand", 0))
            + float(inv.get("in_transit", 0))
            - float(inv.get("reserved", 0))
            - float(inv.get("safety_stock", 0))
        )
        net = max(0.0, gross - available)
        lead = int(item.get("lead_days", 0))
        status = "sufficient"
        if net > 0 and item.get("supplier") != "internal":
            total_purchased += 1
            status = "po_needed"
            if lead >= 7:
                status = "po_critical"
            po_needed.append(
                {
                    "material_id": mid,
                    "qty": round(net, 2),
                    "supplier": item.get("supplier"),
                    "lead_days": lead,
                    "urgency": "critical" if status == "po_critical" else "standard",
                    "agent": "A9",
                }
            )
        elif net <= 0:
            sufficient += 1
        elif item.get("supplier") == "internal":
            status = "make"
            sufficient += 1 if net <= 0 else 0

        lines.append(
            {
                "material_id": mid,
                "level": item.get("level"),
                "parent": item.get("parent"),
                "gross_requirement": round(gross, 2),
                "available": round(available, 2),
                "net_requirement": round(net, 2),
                "lead_days": lead,
                "supplier": item.get("supplier"),
                "status": status,
            }
        )

    return {
        "product_id": product_id,
        "mo_qty": mo_qty,
        "lines": lines,
        "summary": {
            "materials_checked": len(lines),
            "sufficient": sufficient,
            "po_needed": len([p for p in po_needed if p["urgency"] == "standard"]),
            "po_critical": len([p for p in po_needed if p["urgency"] == "critical"]),
            "draft_po_count": len(po_needed),
            "draft_pos": po_needed,
        },
        "planner_action": "review_and_approve_pos" if po_needed else "none",
    }
