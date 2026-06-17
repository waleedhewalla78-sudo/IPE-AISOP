import asyncio

from app.events.handlers import handle_mo_completed
from ipe_shared.events.consumer import KafkaConsumer

_consumer_tasks: list[asyncio.Task] = []


async def start_consumers():
    consumer = KafkaConsumer(
        topics=["ipe.mo.status_changed"],
        group_id="rec-svc",
        handler=handle_mo_completed,
        service_name="rec-svc",
    )
    task = asyncio.create_task(consumer.start())
    _consumer_tasks.append((consumer, task))


async def stop_consumers():
    for consumer, task in _consumer_tasks:
        await consumer.stop()
        task.cancel()
    _consumer_tasks.clear()
