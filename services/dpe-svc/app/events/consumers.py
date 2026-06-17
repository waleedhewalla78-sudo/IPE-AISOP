import asyncio

from app.events.handlers import handle_demand_created
from ipe_shared.events.consumer import KafkaConsumer

_consumer_tasks: list[asyncio.Task] = []


async def start_consumers():
    consumer = KafkaConsumer(
        topics=["ipe.demand.created"],
        group_id="dpe-svc",
        handler=handle_demand_created,
        service_name="dpe-svc",
    )
    task = asyncio.create_task(consumer.start())
    _consumer_tasks.append((consumer, task))


async def stop_consumers():
    for consumer, task in _consumer_tasks:
        await consumer.stop()
        task.cancel()
    _consumer_tasks.clear()
