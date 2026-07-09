import asyncio
import os

from app.events.eib_handler import handle_eib_activity
from app.events.handlers import handle_demand_created
from ipe_shared.events.consumer import KafkaConsumer
from ipe_shared.events.eib import EIB_INGRESS_TOPICS

_consumer_tasks: list = []


def _kafka_enabled() -> bool:
    servers = os.getenv("IPE_KAFKA_BOOTSTRAP_SERVERS") or os.getenv("KAFKA_BOOTSTRAP_SERVERS") or ""
    return bool(servers.strip())


def _make_eib_handler(topic: str):
    async def handler(payload: dict):
        await handle_eib_activity(topic, payload)

    return handler


async def start_consumers():
    if not _kafka_enabled():
        return

    consumer = KafkaConsumer(
        topics=["ipe.demand.created"],
        group_id="dpe-svc",
        handler=handle_demand_created,
        service_name="dpe-svc",
    )
    task = asyncio.create_task(consumer.start())
    _consumer_tasks.append((consumer, task))

    for topic in EIB_INGRESS_TOPICS:
        if topic == "ipe.demand.created":
            continue
        eib_consumer = KafkaConsumer(
            topics=[topic],
            group_id="dpe-svc-eib",
            handler=_make_eib_handler(topic),
            service_name="dpe-svc",
        )
        eib_task = asyncio.create_task(eib_consumer.start())
        _consumer_tasks.append((eib_consumer, eib_task))


async def stop_consumers():
    for consumer, task in _consumer_tasks:
        await consumer.stop()
        task.cancel()
    _consumer_tasks.clear()
