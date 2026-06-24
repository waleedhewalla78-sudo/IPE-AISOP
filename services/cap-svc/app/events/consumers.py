import asyncio

from app.events.handlers import (
    handle_disruption_detected,
    handle_maintenance_block_required,
    handle_operator_absence,
    handle_workcenter_status_changed,
)
from ipe_shared.events.consumer import KafkaConsumer

_consumer_tasks: list[asyncio.Task] = []


async def start_consumers():
    consumer1 = KafkaConsumer(
        topics=["ipe.workcenter.status_changed"],
        group_id="cap-svc",
        handler=handle_workcenter_status_changed,
        service_name="cap-svc",
    )
    consumer2 = KafkaConsumer(
        topics=["ipe.operator.absence"],
        group_id="cap-svc",
        handler=handle_operator_absence,
        service_name="cap-svc",
    )
    consumer3 = KafkaConsumer(
        topics=["ipe.disruption.detected"],
        group_id="cap-svc",
        handler=handle_disruption_detected,
        service_name="cap-svc",
    )
    consumer4 = KafkaConsumer(
        topics=["ipe.maintenance.block_required"],
        group_id="cap-svc",
        handler=handle_maintenance_block_required,
        service_name="cap-svc",
    )
    task1 = asyncio.create_task(consumer1.start())
    task2 = asyncio.create_task(consumer2.start())
    task3 = asyncio.create_task(consumer3.start())
    task4 = asyncio.create_task(consumer4.start())
    _consumer_tasks.extend([(consumer1, task1), (consumer2, task2), (consumer3, task3), (consumer4, task4)])


async def stop_consumers():
    for consumer, task in _consumer_tasks:
        await consumer.stop()
        task.cancel()
    _consumer_tasks.clear()
