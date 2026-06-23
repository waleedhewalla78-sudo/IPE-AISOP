import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.atp import compute_material_score
from app.events.handlers import handle_demand_created, handle_supply_updated
from ipe_shared.database.connection import get_engine
from ipe_shared.events.consumer import KafkaConsumer
from ipe_shared.events.producer import kafka_producer
from ipe_shared.middleware.tenant_context import tenant_ctx

_consumer_tasks: list[asyncio.Task] = []


async def handle_demand_classified(event: dict):
    payload = event.get("payload", event)
    mo_id = payload.get("mo_id", "")
    if not mo_id:
        return

    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return

    engine = get_engine()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        result = await compute_material_score(
            mo_id=UUID(mo_id),
            tenant_id=UUID(tenant_id),
            session=session,
        )

    envelope = kafka_producer.build_envelope(
        "ipe.mo.material_scored", tenant_id, result,
    )
    await kafka_producer.send_avro("ipe.mo.material_scored", key=mo_id, envelope=envelope)

    for comp in result.get("component_breakdown", []):
        if comp.get("on_time_probability", 1.0) < 0.80:
            delay_payload = {
                "mo_id": str(mo_id),
                "component_id": comp["component_id"],
                "on_time_probability": comp["on_time_probability"],
                "required_qty": comp.get("required_qty"),
            }
            delay_envelope = kafka_producer.build_envelope(
                "ipe.supply.delay_detected", tenant_id, delay_payload,
            )
            await kafka_producer.send_avro(
                "ipe.supply.delay_detected",
                key=comp["component_id"],
                envelope=delay_envelope,
            )


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
    consumer3 = KafkaConsumer(
        topics=["ipe.demand.classified"],
        group_id="mat-svc",
        handler=handle_demand_classified,
        service_name="mat-svc",
    )
    task1 = asyncio.create_task(consumer1.start())
    task2 = asyncio.create_task(consumer2.start())
    task3 = asyncio.create_task(consumer3.start())
    _consumer_tasks.extend([
        (consumer1, task1),
        (consumer2, task2),
        (consumer3, task3),
    ])


async def stop_consumers():
    for consumer, task in _consumer_tasks:
        await consumer.stop()
        task.cancel()
    _consumer_tasks.clear()
