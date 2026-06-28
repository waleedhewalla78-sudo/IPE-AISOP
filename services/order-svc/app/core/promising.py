"""ATP/CTP promise calculation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


def compute_atp_promise(
    requested_qty: float,
    on_hand: float,
    *,
    lead_days: int = 7,
) -> dict:
    now = datetime.now(UTC)
    if on_hand >= requested_qty:
        return {
            "promise_type": "ATP",
            "promise_date": now.isoformat(),
            "promised_quantity": requested_qty,
            "confidence_score": 0.95,
        }
    shortfall = requested_qty - on_hand
    days = lead_days + int(min(shortfall / max(requested_qty, 1), 1) * 5)
    return {
        "promise_type": "CTP",
        "promise_date": (now + timedelta(days=days)).isoformat(),
        "promised_quantity": requested_qty,
        "confidence_score": 0.75,
        "shortfall": shortfall,
    }
