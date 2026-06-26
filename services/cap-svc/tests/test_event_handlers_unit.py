"""Event handler unit tests — R2-01."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.events.handlers import handle_workcenter_status_changed


@pytest.mark.asyncio
async def test_handle_workcenter_status_changed_emits_bottleneck():
    tenant_id = str(uuid4())
    envelope_data = {
        "event_id": str(uuid4()),
        "event_type": "ipe.workcenter.status_changed",
        "source": "iot-svc",
        "tenant_id": tenant_id,
        "timestamp": "2026-06-01T00:00:00Z",
        "data": {"work_center_id": "WC-001", "status": "degraded"},
        "correlation_id": str(uuid4()),
    }

    with patch("app.events.handlers.kafka_producer") as producer:
        producer.send_event = AsyncMock()
        await handle_workcenter_status_changed(envelope_data)

    producer.send_event.assert_awaited_once()
    call_kwargs = producer.send_event.await_args.kwargs
    assert call_kwargs["key"] == "WC-001"


@pytest.mark.asyncio
async def test_handle_workcenter_status_changed_ignores_invalid():
    with patch("app.events.handlers.kafka_producer") as producer:
        producer.send_event = AsyncMock()
        await handle_workcenter_status_changed("not-a-dict")
    producer.send_event.assert_not_awaited()
