import asyncio
import logging

from ipe_shared.events.consumer import KafkaConsumer

logger = logging.getLogger(__name__)

_consumer_tasks: list[tuple[KafkaConsumer, asyncio.Task]] = []


async def _handle_copilot_chat(event: dict):
    """Handle copilot chat events for logging and analytics."""
    logger.info("Copilot chat event received: %s", event.get("event_id", "unknown"))


async def start_consumers():
    """Start Kafka consumers for nlp-svc."""
    consumer = KafkaConsumer(
        topics=["ipe.copilot.chat"],
        group_id="nlp-svc",
        handler=_handle_copilot_chat,
        service_name="nlp-svc",
    )
    task = asyncio.create_task(consumer.start())
    _consumer_tasks.append((consumer, task))


async def stop_consumers():
    """Stop all Kafka consumers."""
    for consumer, task in _consumer_tasks:
        await consumer.stop()
        task.cancel()
    _consumer_tasks.clear()
