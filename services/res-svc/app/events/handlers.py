from datetime import UTC, datetime
from uuid import uuid4

from app.core.business_score import score_scenario
from app.core.strategy import generate_strategies
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope


async def handle_feasibility_scored(event: dict):
    value = event.value if hasattr(event, "value") else event
    if isinstance(value, dict):
        envelope = EventEnvelope(**value)
    else:
        return

    data = envelope.data
    mo_id = str(data.get("mo_id") or data.get("demand_line_id") or "")
    if not mo_id:
        return

    score = data.get("feasibility_score")
    if score is not None and float(score) >= 75.0:
        return
    if data.get("is_feasible") is True and score is None:
        return

    constraint = data.get("primary_constraint") or "capacity_overload"

    strategies = generate_strategies(mo_id, constraint)
    best = None
    best_score = -1
    for s in strategies:
        scored = score_scenario(s)
        if scored["business_score"] > best_score:
            best_score = scored["business_score"]
            best = s

    await kafka_producer.send_event(
        "resolution", "proposed",
        key=mo_id,
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.resolution.proposed",
            source="res-svc",
            tenant_id=envelope.tenant_id,
            timestamp=datetime.now(UTC),
            data={
                "mo_id": mo_id,
                "constraint_type": constraint,
                "scenario_count": len(strategies),
                "recommended_strategy": best["strategy"] if best else None,
                "recommended_score": best_score if best_score > -1 else None,
            },
            correlation_id=envelope.correlation_id,
        ).model_dump(mode="json"),
    )
