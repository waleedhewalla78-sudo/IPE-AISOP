"""Supply network → demand forecast confidence adjustment."""

from __future__ import annotations

SUPPLY_NETWORK_TOPIC = "ipe.supply.network.updated"
SUPPLY_ADJUSTED_TOPIC = "ipe.supply.adjusted"


def adjust_forecast_for_supply(
    base_value: float,
    *,
    capacity_utilization_pct: float,
    lead_time_days: float,
) -> tuple[float, float]:
    """Return (adjusted_value, confidence_score) after supply constraints."""
    capacity_factor = max(0.5, 1.0 - max(0.0, capacity_utilization_pct - 70) / 100)
    lead_time_factor = max(0.6, 1.0 - min(lead_time_days, 30) / 60)
    confidence = round(min(1.0, capacity_factor * lead_time_factor), 4)
    adjusted = round(base_value * confidence, 4)
    return adjusted, confidence


def parse_supply_network_event(payload: dict) -> dict:
    """Normalize Kafka supply network update payload."""
    return {
        "tenant_id": payload.get("tenant_id", ""),
        "capacity_utilization_pct": float(payload.get("capacity_utilization_pct", 75.0)),
        "lead_time_days": float(payload.get("lead_time_days", 7.0)),
        "facilities_count": int(payload.get("facilities_count", 0)),
    }
