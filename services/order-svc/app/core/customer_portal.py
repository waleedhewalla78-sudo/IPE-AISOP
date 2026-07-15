"""A8 customer portal helpers (read-only order tracking)."""

from __future__ import annotations

from typing import Any


STATUS_PIPELINE = ("confirmed", "in_production", "testing", "shipped", "delivered")


def map_order_status(raw: str | None) -> str:
    raw = (raw or "open").lower()
    mapping = {
        "open": "confirmed",
        "promised": "confirmed",
        "in_progress": "in_production",
        "producing": "in_production",
        "testing": "testing",
        "shipped": "shipped",
        "delivered": "delivered",
        "closed": "delivered",
        "exception": "in_production",
    }
    return mapping.get(raw, "confirmed")


def delivery_confidence(days_to_due: int | None, otd_risk: float = 0.0) -> dict[str, Any]:
    if days_to_due is None:
        level, color = "unknown", "amber"
    elif days_to_due >= 3 and otd_risk < 0.2:
        level, color = "on_track", "green"
    elif days_to_due >= 0 or otd_risk < 0.4:
        level, color = "minor_risk", "amber"
    else:
        level, color = "at_risk", "red"
    return {"confidence": level, "color": color, "days_to_due": days_to_due, "otd_risk": otd_risk}


def build_portal_summary(orders: list[dict[str, Any]]) -> dict[str, Any]:
    items = []
    for o in orders:
        status = map_order_status(o.get("status"))
        conf = delivery_confidence(o.get("days_to_due"), float(o.get("otd_risk") or 0))
        items.append(
            {
                "order_id": o.get("id") or o.get("order_id"),
                "order_number": o.get("order_number"),
                "status": status,
                "delivery_date": o.get("promised_date") or o.get("requested_date"),
                "invoice_status": o.get("invoice_status", "pending"),
                **conf,
            }
        )
    return {
        "agent_id": "A8",
        "read_only": True,
        "orders": items,
        "active_count": len([i for i in items if i["status"] != "delivered"]),
    }
