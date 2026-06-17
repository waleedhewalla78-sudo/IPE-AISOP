from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.netting import cumulative_netting
from ipe_shared.database.connection import get_engine
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope


async def handle_demand_created(event: dict):
    value = event.value if hasattr(event, "value") else event
    if isinstance(value, dict):
        envelope = EventEnvelope(**value)
    else:
        return

    data = envelope.data
    product_id = data.get("product_id", "")
    quantity = float(data.get("quantity", 1))

    engine = get_engine()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        result = await cumulative_netting(
            session, envelope.tenant_id,
            UUID(product_id), quantity, None,
        )

    if result.get("shortage_quantity", 0) > 0:
        await kafka_producer.send_event(
            "supply", "delay_detected",
            key=product_id,
            value=EventEnvelope(
                event_id=str(uuid4()),
                event_type="ipe.supply.delay_detected",
                source="mat-svc",
                tenant_id=envelope.tenant_id,
                timestamp=datetime.now(UTC),
                data={
                    "product_id": product_id,
                    "demand_quantity": quantity,
                    "available_quantity": result.get("available_quantity", 0),
                    "shortage_quantity": result.get("shortage_quantity", 0),
                },
                correlation_id=envelope.correlation_id,
            ).model_dump(mode="json"),
        )


async def handle_supply_updated(event: dict):
    value = event.value if hasattr(event, "value") else event
    if isinstance(value, dict):
        envelope = EventEnvelope(**value)
    else:
        return

    data = envelope.data
    product_id = data.get("product_id", "")
    await kafka_producer.send_event(
        "inventory", "changed",
        key=product_id,
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.inventory.changed",
            source="mat-svc",
            tenant_id=envelope.tenant_id,
            timestamp=datetime.now(UTC),
            data={"product_id": product_id, "source": "supply_updated"},
            correlation_id=envelope.correlation_id,
        ).model_dump(mode="json"),
    )
