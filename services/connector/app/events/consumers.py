import asyncio

from app.events.handlers import (
    handle_demand_classified,
    handle_feasibility_scored,
    handle_mo_auto_confirmed,
    handle_po_suggested,
    handle_reconciliation_completed,
    handle_resolution_approved,
    handle_schedule_approved,
    handle_tariff_shock,
)
from ipe_shared.events.consumer import KafkaConsumer

_consumer_tasks: list[tuple[KafkaConsumer, asyncio.Task]] = []


async def start_consumers():
    consumers = [
        KafkaConsumer(
            topics=["ipe.mo.auto_confirmed"],
            group_id="ipe-odoo-connector",
            handler=handle_mo_auto_confirmed,
            service_name="ipe-odoo-connector",
        ),
        KafkaConsumer(
            topics=["ipe.mo.feasibility_scored"],
            group_id="ipe-odoo-connector",
            handler=handle_feasibility_scored,
            service_name="ipe-odoo-connector",
        ),
        KafkaConsumer(
            topics=["ipe.reconciliation.completed"],
            group_id="ipe-odoo-connector",
            handler=handle_reconciliation_completed,
            service_name="ipe-odoo-connector",
        ),
        KafkaConsumer(
            topics=["ipe.demand.classified"],
            group_id="ipe-odoo-connector",
            handler=handle_demand_classified,
            service_name="ipe-odoo-connector",
        ),
        KafkaConsumer(
            topics=["ipe.resolution.approved"],
            group_id="ipe-odoo-connector",
            handler=handle_resolution_approved,
            service_name="ipe-odoo-connector",
        ),
        KafkaConsumer(
            topics=["ipe.po.suggested"],
            group_id="ipe-odoo-connector",
            handler=handle_po_suggested,
            service_name="ipe-odoo-connector",
        ),
        KafkaConsumer(
            topics=["ipe.schedule.approved"],
            group_id="ipe-odoo-connector",
            handler=handle_schedule_approved,
            service_name="ipe-odoo-connector",
        ),
        KafkaConsumer(
            topics=["ipe.tariff.shock"],
            group_id="ipe-odoo-connector",
            handler=handle_tariff_shock,
            service_name="ipe-odoo-connector",
        ),
    ]

    for consumer in consumers:
        task = asyncio.create_task(consumer.start())
        _consumer_tasks.append((consumer, task))


async def stop_consumers():
    for consumer, task in _consumer_tasks:
        await consumer.stop()
        task.cancel()
    _consumer_tasks.clear()
