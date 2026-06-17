from datetime import UTC, datetime
from uuid import uuid4

from app.core.scorer import calculate_feasibility
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope


async def handle_demand_classified(event: dict):
    value = event.value if hasattr(event, "value") else event
    if isinstance(value, dict):
        envelope = EventEnvelope(**value)
    else:
        return

    data = envelope.data

    score_result = calculate_feasibility(
        material_score=data.get("material_score", 0.8),
        capacity_score=data.get("capacity_score", 0.8),
        labor_score=data.get("labor_score", 0.8),
        historical_reliability=data.get("historical_score", 0.5),
    )

    await kafka_producer.send_event(
        "mo", "feasibility_scored",
        key=str(data.get("demand_line_id", "")),
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.mo.feasibility_scored",
            source="fea-svc",
            tenant_id=envelope.tenant_id,
            timestamp=datetime.now(UTC),
            data={
                "demand_line_id": str(data.get("demand_line_id", "")),
                "overall_score": score_result["overall_score"],
                "is_feasible": score_result["is_feasible"],
                "primary_constraint": score_result.get("primary_constraint"),
                "risk_level": score_result.get("risk_level", "medium"),
            },
            correlation_id=envelope.correlation_id,
        ).model_dump(mode="json"),
    )
