import pytest

from app.core.capacity_auction import CapacityAuction
from app.core.smart_batcher import SmartBatcher


@pytest.mark.asyncio
async def test_smart_batcher_saves_changeover():
    batcher = SmartBatcher()
    mos = [
        {
            "id": "mo-1",
            "product_id": "DT100",
            "product_family": "DT",
            "planned_start": "2026-07-15",
            "planned_end": "2026-07-18",
            "work_centre_id": "wc-1",
        },
        {
            "id": "mo-2",
            "product_id": "PT500",
            "product_family": "PT",
            "planned_start": "2026-07-16",
            "planned_end": "2026-07-19",
            "work_centre_id": "wc-1",
        },
        {
            "id": "mo-3",
            "product_id": "DT100",
            "product_family": "DT",
            "planned_start": "2026-07-17",
            "planned_end": "2026-07-20",
            "work_centre_id": "wc-1",
        },
    ]
    results = await batcher.optimize_batches(
        None, "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", mos, [{"id": "wc-1", "name": "Winding"}]
    )
    assert results
    assert results[0]["savings_min"] >= 0
    assert results[0]["delivery_dates_maintained"] is True


@pytest.mark.asyncio
async def test_capacity_auction_picks_higher_priority():
    auction = CapacityAuction()
    result = await auction.resolve_conflict(
        None,
        "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        [
            {
                "id": "mo-a",
                "number": "MO-A",
                "margin_pct": 40,
                "penalty_per_day": 2000,
                "order_value": 28000,
                "customer_priority": "A",
                "days_to_deadline": 5,
            },
            {
                "id": "mo-b",
                "number": "MO-B",
                "margin_pct": 20,
                "penalty_per_day": 500,
                "order_value": 15000,
                "customer_priority": "B",
                "days_to_deadline": 12,
            },
        ],
        {"duration_days": 1},
    )
    assert result["winner"]["mo_id"] == "mo-a"
    assert len(result["reschedule_plan"]) == 1
    assert "rationale" in result
