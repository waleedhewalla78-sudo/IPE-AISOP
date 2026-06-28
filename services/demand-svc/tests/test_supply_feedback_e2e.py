"""Supply feedback consumer — unit and handler tests."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.consumers.supply_feedback_consumer import handle_supply_adjustment
from app.core.supply_feedback import SUPPLY_ADJUSTED_TOPIC
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.v8_planning import DemandForecast

DEMO_TENANT = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
PRODUCT_ID = "abdc613f-643c-4395-a4c7-f6748debe126"


@pytest.mark.asyncio
async def test_handle_supply_adjustment_persists_forecast():
    session = AsyncMock()
    added: list = []

    def _capture(obj):
        added.append(obj)

    session.add = MagicMock(side_effect=_capture)
    token = tenant_ctx.set(DEMO_TENANT)
    try:
        await handle_supply_adjustment(
            session,
            {
                "tenant_id": DEMO_TENANT,
                "product_id": PRODUCT_ID,
                "base_value": 100.0,
                "capacity_utilization_pct": 90.0,
                "lead_time_days": 14.0,
            },
        )
    finally:
        tenant_ctx.reset(token)

    assert len(added) == 1
    row = added[0]
    assert isinstance(row, DemandForecast)
    assert row.model_version == "supply_adjusted"
    assert row.tenant_id == UUID(DEMO_TENANT)
    assert row.product_id == UUID(PRODUCT_ID)
    assert float(row.value) < 100.0


def test_supply_adjusted_topic_constant():
    assert SUPPLY_ADJUSTED_TOPIC == "ipe.supply.adjusted"
