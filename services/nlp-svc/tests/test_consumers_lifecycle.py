"""NLP Kafka consumer lifecycle tests (P8 R1-01)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.events import consumers


@pytest.mark.asyncio
async def test_handle_copilot_chat_logs():
    with patch("app.events.consumers.logger") as log:
        await consumers._handle_copilot_chat({"event_id": "e1"})
        log.info.assert_called_once()


@pytest.mark.asyncio
async def test_start_and_stop_consumers():
    mock_consumer = MagicMock()
    mock_consumer.start = AsyncMock()
    mock_consumer.stop = AsyncMock()
    mock_task = MagicMock()
    mock_task.cancel = MagicMock()

    with (
        patch("app.events.consumers.KafkaConsumer", return_value=mock_consumer),
        patch("app.events.consumers.asyncio.create_task", return_value=mock_task),
    ):
        consumers._consumer_tasks.clear()
        await consumers.start_consumers()
        assert len(consumers._consumer_tasks) == 1
        await consumers.stop_consumers()
        assert len(consumers._consumer_tasks) == 0
