"""Mat event handler unit tests — R2-02."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.events.handlers import handle_demand_created


@pytest.mark.asyncio
async def test_handle_demand_created_emits_shortage_event():
    tenant_id = uuid4()
    product_id = str(uuid4())
    envelope = {
        "event_id": str(uuid4()),
        "event_type": "ipe.demand.created",
        "source": "dpe-svc",
        "tenant_id": str(tenant_id),
        "timestamp": datetime.now(UTC).isoformat(),
        "data": {"product_id": product_id, "quantity": 100},
        "correlation_id": str(uuid4()),
    }

    with patch("app.events.handlers.cumulative_netting", new_callable=AsyncMock) as mock_net, patch(
        "app.events.handlers.get_engine", return_value=MagicMock()
    ), patch("app.events.handlers.async_sessionmaker") as mock_sm, patch(
        "app.events.handlers.kafka_producer"
    ) as producer:
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_sm.return_value = MagicMock(return_value=mock_session)

        mock_net.return_value = {"shortage_quantity": 25, "available_quantity": 75}
        producer.send_event = AsyncMock()

        await handle_demand_created(envelope)

    producer.send_event.assert_awaited_once()
    assert producer.send_event.await_args.kwargs["value"]["event_type"] == "ipe.supply.delay_detected"
