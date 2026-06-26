"""DPE demand handler success path — R2-03."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.events.handlers import handle_demand_created


@pytest.mark.asyncio
async def test_handle_demand_created_sets_priority(monkeypatch):
    demand_line = MagicMock()
    demand_line.customer_tier = 1
    demand_line.margin_pct = 0.2
    demand_line.required_date = datetime.now(UTC)
    demand_line.penalty_cost = 100
    demand_line.mo_id = None
    demand_line.product_id = uuid4()
    demand_line.quantity = 5
    demand_line.priority_score = None

    product = MagicMock(category_tags=["A"])

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(
        side_effect=[
            MagicMock(),
            MagicMock(one_or_none=MagicMock(return_value=(demand_line, product))),
            MagicMock(fetchone=MagicMock(return_value=(uuid4(),))),
        ]
    )
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_factory = MagicMock(return_value=mock_session)
    mock_ctx = MagicMock()
    mock_ctx.get.return_value = str(uuid4())

    with patch("app.events.handlers.kafka_producer") as producer:
        producer.build_envelope = MagicMock(return_value={"event_type": "ipe.demand.classified"})
        producer.send_avro = AsyncMock()

        monkeypatch.setattr("app.events.handlers.get_engine", lambda: MagicMock())
        monkeypatch.setattr("app.events.handlers.async_sessionmaker", lambda *a, **k: mock_factory)
        monkeypatch.setattr("app.events.handlers.tenant_ctx", mock_ctx)

        await handle_demand_created({"demand_line_id": str(uuid4())})

    assert demand_line.priority_score is not None
    mock_session.commit.assert_awaited()
    producer.send_avro.assert_awaited_once()
