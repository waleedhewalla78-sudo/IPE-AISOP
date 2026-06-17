import asyncio

from app.events.handlers import handle_demand_created, handle_supply_updated
from ipe_shared.events.consumer import KafkaConsumer

_consumer_tasks: list[asyncio.Task] = []


async def start_consumers():
    consumer1 = KafkaConsumer(
        topics=["ipe.demand.created"],
        group_id="mat-svc",
        handler=handle_demand_created,
        service_name="mat-svc",
    )
    consumer2 = KafkaConsumer(
        topics=["ipe.supply.updated"],
        group_id="mat-svc",
        handler=handle_supply_updated,
        service_name="mat-svc",
    )
    task1 = asyncio.create_task(consumer1.start())
    task2 = asyncio.create_task(consumer2.start())
    _consumer_tasks.extend([(consumer1, task1), (consumer2, task2)])


async def stop_consumers():
    for consumer, task in _consumer_tasks:
        await consumer.stop()
        task.cancel()
    _consumer_tasks.clear()
