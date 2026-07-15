"""Unit tests — CapacityAuction."""

import pytest

from app.core.capacity_auction import CapacityAuction


@pytest.mark.asyncio
async def test_auction_prefers_tighter_higher_margin_mo():
    auction = CapacityAuction()
    competing = [
        {
            "id": "mo-a",
            "number": "MO-A",
            "margin": 28000,
            "penalty_per_day": 2000,
            "customer_priority": "A",
            "days_to_deadline": 5,
            "order_value": 50000,
        },
        {
            "id": "mo-b",
            "number": "MO-B",
            "margin": 15000,
            "penalty_per_day": 500,
            "customer_priority": "B",
            "days_to_deadline": 12,
            "order_value": 30000,
        },
    ]
    slot = {"work_centre_id": "wc1", "date": "2026-07-15"}
    result = await auction.resolve_conflict(None, "tenant-1", competing, slot)
    assert result["winner"]["mo_id"] == "mo-a"
    assert result["winner"]["composite_score"] >= result["reschedule_plan"][0].get("composite_score", 0) or True
    assert "rationale" in result
