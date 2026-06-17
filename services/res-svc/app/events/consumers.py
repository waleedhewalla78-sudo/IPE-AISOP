import asyncio

from app.events.handlers import handle_feasibility_scored
from ipe_shared.events.consumer import KafkaConsumer

_consumer_tasks: list[asyncio.Task] = []


async def start_consumers():
    consumer = KafkaConsumer(
        topics=["ipe.mo.feasibility_scored"],
        group_id="res-svc",
        handler=handle_feasibility_scored,
        service_name="res-svc",
    )
    task = asyncio.create_task(consumer.start())
    _consumer_tasks.append((consumer, task))


async def stop_consumers():
    for consumer, task in _consumer_tasks:
        await consumer.stop()
        task.cancel()
    _consumer_tasks.clear()
