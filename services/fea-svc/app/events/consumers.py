import asyncio

from app.events.handlers import handle_capacity_scored, handle_material_scored
from ipe_shared.events.consumer import KafkaConsumer

_consumer_tasks: list[asyncio.Task] = []


async def start_consumers():
    material_consumer = KafkaConsumer(
        topics=["ipe.mo.material_scored"],
        group_id="fea-svc",
        handler=handle_material_scored,
        service_name="fea-svc",
    )
    capacity_consumer = KafkaConsumer(
        topics=["ipe.mo.capacity_scored"],
        group_id="fea-svc",
        handler=handle_capacity_scored,
        service_name="fea-svc",
    )
    task1 = asyncio.create_task(material_consumer.start())
    task2 = asyncio.create_task(capacity_consumer.start())
    _consumer_tasks.extend([(material_consumer, task1), (capacity_consumer, task2)])


async def stop_consumers():
    for consumer, task in _consumer_tasks:
        await consumer.stop()
        task.cancel()
    _consumer_tasks.clear()
