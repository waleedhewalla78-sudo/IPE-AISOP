from datetime import UTC, datetime
from uuid import uuid4

from app.core.rule_classifier import classify_by_rules
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope


async def handle_work_order_delayed(event: dict):
    value = event.value if hasattr(event, "value") else event
    if isinstance(value, dict):
        envelope = EventEnvelope(**value)
    else:
        return

    data = envelope.data
    classification = classify_by_rules(data)

    await kafka_producer.send_event(
        "delay", "classified",
        key=data.get("mo_id", ""),
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.delay.classified",
            source="del-svc",
            tenant_id=envelope.tenant_id,
            timestamp=datetime.now(UTC),
            data={
                "mo_id": data.get("mo_id", ""),
                "cause_category": classification["cause_category"],
                "confidence": classification["confidence"],
                "matched_keywords": classification.get("matched_keywords", []),
            },
            correlation_id=envelope.correlation_id,
        ).model_dump(mode="json"),
    )
