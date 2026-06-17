from datetime import UTC, datetime
from uuid import uuid4

from app.core.classifier import classify_demand_type
from app.core.priority import calculate_priority
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope


async def handle_demand_created(event: dict):
    value = event.value if hasattr(event, "value") else event
    if isinstance(value, dict):
        envelope = EventEnvelope(**value)
    else:
        return

    data = envelope.data

    product_data = {
        "source_type": data.get("source_type", "manufactured"),
        "lead_time_days": float(data.get("lead_time_days", 0)),
        "safety_stock": float(data.get("safety_stock", 0)),
        "demand_cv": float(data.get("demand_cv", 0.3)),
    }
    customer_tier = int(data.get("customer_tier", 3))

    demand_type = classify_demand_type(
        product_data=product_data,
        customer_tier=customer_tier,
    )

    priority = calculate_priority({
        "required_date": data.get("required_date", datetime.now(UTC).isoformat()),
        "customer_tier": customer_tier,
        "penalty_cost": float(data.get("penalty_cost", 0)),
        "margin_pct": float(data.get("margin_pct", 25)),
        "quantity": float(data.get("quantity", 1)),
    })

    classified = {
        "demand_line_id": str(data.get("demand_line_id", "")),
        "product_id": str(data.get("product_id", "")),
        "demand_type": demand_type["demand_type"],
        "priority_score": priority["priority_score"],
        "is_urgent": priority["is_urgent"],
        "composite_score": priority["composite_score"],
        "classifier_reason": demand_type.get("reason", ""),
    }

    await kafka_producer.send_event(
        "demand", "classified",
        key=str(data.get("product_id", "")),
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.demand.classified",
            source="dpe-svc",
            tenant_id=envelope.tenant_id,
            timestamp=datetime.now(UTC),
            data=classified,
            correlation_id=envelope.correlation_id,
        ).model_dump(mode="json"),
    )


async def handle_inventory_changed(event: dict):
    pass
