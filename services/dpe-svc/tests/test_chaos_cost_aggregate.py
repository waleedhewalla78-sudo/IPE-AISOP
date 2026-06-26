"""Chaos cost aggregation with mocked DB — R2-03."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.chaos_cost import aggregate_chaos_cost


def _delay_event(cause="machine_breakdown", cost=None, minutes=10):
    ev = MagicMock()
    ev.cause_category = cause
    ev.cost_impact = cost
    ev.delay_minutes = minutes
    ev.mo_id = uuid4()
    ev.created_at = datetime.now(UTC)
    return ev


def _audit_entry(action="schedule_override", usd=500):
    entry = MagicMock()
    entry.action = action
    entry.after_state = {"cost_impact_usd": usd}
    entry.timestamp = datetime.now(UTC)
    return entry


@pytest.mark.asyncio
async def test_aggregate_chaos_cost_with_delays_and_audit():
    session = AsyncMock()
    delay_result = MagicMock()
    delay_result.scalars.return_value.all.return_value = [
        _delay_event(cost=Decimal("100")),
        _delay_event(cause="quality", cost=None, minutes=20),
    ]
    audit_result = MagicMock()
    audit_result.scalars.return_value.all.return_value = [_audit_entry()]

    disruption_result = MagicMock()
    disruption_result.scalars.return_value.all.return_value = []

    session.execute = AsyncMock(side_effect=[delay_result, audit_result, disruption_result])

    tenant_id = uuid4()
    result = await aggregate_chaos_cost(session, tenant_id, period_days=7)

    assert result["total_chaos_usd"] > 0
    assert len(result["categories"]) >= 1
    assert result["top_mos"]


@pytest.mark.asyncio
async def test_aggregate_chaos_cost_category_filter():
    session = AsyncMock()
    delay_result = MagicMock()
    delay_result.scalars.return_value.all.return_value = [_delay_event()]
    audit_result = MagicMock()
    audit_result.scalars.return_value.all.return_value = []
    disruption_result = MagicMock()
    disruption_result.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(side_effect=[delay_result, audit_result, disruption_result])

    result = await aggregate_chaos_cost(session, uuid4(), category_filter="idle_time")
    assert all(c["code"] == "idle_time" for c in result["categories"])
