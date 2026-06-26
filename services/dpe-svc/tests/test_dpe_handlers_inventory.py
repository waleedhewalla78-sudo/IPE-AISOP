"""Inventory change handler — R2-03."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.events.handlers import handle_inventory_changed


@pytest.mark.asyncio
async def test_handle_inventory_changed_rescores_demands(monkeypatch):
    product_id = str(uuid4())
    demand_line = MagicMock()
    demand_line.customer_tier = 2
    demand_line.margin_pct = 0.15
    demand_line.required_date = datetime.now(UTC)
    demand_line.penalty_cost = 50
    demand_line.priority_score = 40.0

    product = MagicMock(category_tags=["premium"])

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(
        side_effect=[
            MagicMock(),
            MagicMock(all=MagicMock(return_value=[(demand_line, product)])),
        ]
    )
    mock_session.commit = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_factory = MagicMock(return_value=mock_session)
    mock_ctx = MagicMock()
    mock_ctx.get.return_value = str(uuid4())

    monkeypatch.setattr("app.events.handlers.get_engine", lambda: MagicMock())
    monkeypatch.setattr("app.events.handlers.async_sessionmaker", lambda *a, **k: mock_factory)
    monkeypatch.setattr("app.events.handlers.tenant_ctx", mock_ctx)

    await handle_inventory_changed({"product_id": product_id})

    assert demand_line.priority_score != 40.0
    mock_session.commit.assert_awaited()
