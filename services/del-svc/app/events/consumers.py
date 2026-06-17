import asyncio

from app.events.handlers import handle_work_order_delayed
from ipe_shared.events.consumer import KafkaConsumer

_consumer_tasks: list[asyncio.Task] = []


async def start_consumers():
    consumer = KafkaConsumer(
        topics=["ipe.delay.logged"],
        group_id="del-svc",
        handler=handle_work_order_delayed,
        service_name="del-svc",
    )
    task = asyncio.create_task(consumer.start())
    _consumer_tasks.append((consumer, task))


async def stop_consumers():
    for consumer, task in _consumer_tasks:
        await consumer.stop()
        task.cancel()
    _consumer_tasks.clear()
