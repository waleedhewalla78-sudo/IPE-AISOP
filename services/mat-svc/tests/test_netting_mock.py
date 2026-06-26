"""Netting async paths with mocked session — R2-02."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.netting import cumulative_netting, get_current_inventory


@pytest.mark.asyncio
async def test_get_current_inventory_empty():
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    inv = await get_current_inventory(session, uuid4(), uuid4())
    assert inv["qty_on_hand"] == 0


@pytest.mark.asyncio
async def test_cumulative_netting_shortage():
    session = AsyncMock()
    inv_row = MagicMock(qty_on_hand=10, qty_reserved=5)
    supply_row = MagicMock(
        quantity_ordered=20,
        quantity_received=0,
        expected_date=datetime(2026, 7, 1, tzinfo=UTC),
        status="confirmed",
    )
    supplier = None

    call_count = 0

    async def execute_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return MagicMock(scalar_one_or_none=MagicMock(return_value=inv_row))
        if call_count == 2:
            return MagicMock(__iter__=lambda s: iter([(supply_row, supplier)]))
        return MagicMock()

    session.execute = AsyncMock(side_effect=execute_side_effect)
    result = await cumulative_netting(session, uuid4(), uuid4(), demand_quantity=30.0)
    assert result["is_available"] is False
    assert result["shortage_quantity"] > 0
