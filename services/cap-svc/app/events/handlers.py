from datetime import UTC, datetime
from uuid import uuid4

from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope


async def handle_workcenter_status_changed(event: dict):
    value = event.value if hasattr(event, "value") else event
    if isinstance(value, dict):
        envelope = EventEnvelope(**value)
    else:
        return
    data = envelope.data
    wc_id = data.get("work_center_id", data.get("id", "unknown"))
    await kafka_producer.send_event(
        "workcenter", "bottleneck_detected",
        key=wc_id,
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.workcenter.bottleneck_detected",
            source="cap-svc",
            tenant_id=envelope.tenant_id,
            timestamp=datetime.now(UTC),
            data={
                "work_center_id": wc_id,
                "status": data.get("status", "unknown"),
                "message": f"Work center {wc_id} status changed to {data.get('status', 'unknown')}",
            },
            correlation_id=envelope.correlation_id,
        ).model_dump(mode="json"),
    )


async def handle_operator_absence(event: dict):
    value = event.value if hasattr(event, "value") else event
    if isinstance(value, dict):
        envelope = EventEnvelope(**value)
    else:
        return
    data = envelope.data
    operator_id = data.get("operator_id", "unknown")
    await kafka_producer.send_event(
        "delay", "logged",
        key=operator_id,
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.delay.logged",
            source="cap-svc",
            tenant_id=envelope.tenant_id,
            timestamp=datetime.now(UTC),
            data={
                "source_text": f"Operator absence: {operator_id}",
                "cause_category": "labor_absence",
                "confidence": 0.85,
                "mo_id": data.get("mo_id", ""),
            },
            correlation_id=envelope.correlation_id,
        ).model_dump(mode="json"),
    )
