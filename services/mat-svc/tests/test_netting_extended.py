"""Extended netting + contention tests — R2-02."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.netting import (
    detect_contentions,
    get_bom_requirements,
    get_open_supply,
    priority_weighted_netting,
)


@pytest.mark.asyncio
async def test_get_open_supply_with_supplier_delay():
    session = AsyncMock()
    supply = MagicMock(
        id=uuid4(),
        quantity_ordered=100,
        quantity_received=10,
        expected_date=datetime(2026, 8, 1, tzinfo=UTC),
        status="confirmed",
    )
    supplier = MagicMock(avg_delay_days=Decimal("2"), delay_std_dev_days=Decimal("0.5"))
    supplier.name = "Acme"
    session.execute = AsyncMock(
        return_value=MagicMock(__iter__=lambda s: iter([(supply, supplier)]))
    )
    rows = await get_open_supply(session, uuid4(), uuid4())
    assert len(rows) == 1
    assert rows[0]["supplier_name"] == "Acme"
    assert rows[0]["expected_delay_days"] >= 0


@pytest.mark.asyncio
async def test_get_bom_requirements():
    session = AsyncMock()
    bline = MagicMock(
        component_id=uuid4(),
        quantity_per=2.0,
        scrap_rate_pct=5.0,
        is_critical=True,
    )
    session.execute = AsyncMock(
        return_value=MagicMock(__iter__=lambda s: iter([(bline, MagicMock())]))
    )
    rows = await get_bom_requirements(session, uuid4(), uuid4())
    assert rows[0]["quantity_per"] == 2.0
    assert rows[0]["is_critical"] is True


@pytest.mark.asyncio
async def test_priority_weighted_netting_allocations():
    tid = uuid4()
    pid = uuid4()
    inv_row = MagicMock(qty_on_hand=50, qty_reserved=10)

    async def execute_side_effect(*args, **kwargs):
        sql = str(args[0]) if args else ""
        if "InventoryPosition" in sql or "inventory" in sql.lower():
            return MagicMock(scalar_one_or_none=MagicMock(return_value=inv_row))
        if "SupplyOrder" in sql or "supply" in sql.lower():
            return MagicMock(__iter__=lambda s: iter([]))
        if "BomLine" in sql or "bom" in sql.lower():
            return MagicMock(__iter__=lambda s: iter([]))
        return MagicMock()

    session = AsyncMock()
    session.execute = AsyncMock(side_effect=execute_side_effect)

    demands = [
        {"id": "d1", "quantity": 30, "demand_type": "MTO", "priority_score": 0.9},
        {"id": "d2", "quantity": 20, "demand_type": "MTS", "priority_score": 0.5},
    ]
    result = await priority_weighted_netting(session, tid, pid, demands)
    assert len(result["allocations"]) == 2
    assert result["allocations"][0]["demand_type"] == "MTO"


@pytest.mark.asyncio
async def test_detect_contentions_shortage_and_overlap():
    session = AsyncMock()
    demands = [
        {"quantity": 100, "priority_score": 0.9},
        {"quantity": 80, "priority_score": 0.85},
    ]
    supply_orders = [{"quantity_ordered": 50, "quantity_received": 0}]
    contentions = await detect_contentions(session, uuid4(), uuid4(), demands, supply_orders)
    types = {c["type"] for c in contentions}
    assert "cumulative_shortage" in types
    assert "urgent_demand_overlap" in types
