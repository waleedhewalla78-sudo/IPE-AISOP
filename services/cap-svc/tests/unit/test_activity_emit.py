"""Sprint 7 T718 — cap-svc activity emit on schedule created."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from ipe_shared.events.eib import build_summary, normalize_kafka_message


def test_schedule_created_topic_parses():
    from ipe_shared.events.eib import parse_kafka_topic

    tool, event = parse_kafka_topic("ipe.schedule.created")
    assert tool == "schedule"
    assert event == "created"


def test_schedule_summary_includes_mo_count():
    summary = build_summary(
        "schedule",
        "created",
        {"summary": "Schedule created for 3 MO(s) (OPTIMAL)"},
    )
    assert "3" in summary


def test_normalize_schedule_envelope():
    tenant_id = str(uuid4())
    envelope = {
        "tenant_id": tenant_id,
        "event_id": "sched-1",
        "payload": {
            "summary": "Schedule created for 2 MO(s) (OPTIMAL)",
            "mo_count": 2,
            "solver_status": "OPTIMAL",
        },
    }
    row = normalize_kafka_message("ipe.schedule.created", envelope)
    assert row["source_tool"] == "schedule"
    assert row["event_type"] == "created"


@pytest.mark.asyncio
async def test_emit_schedule_created_activity_persists():
    from app.core.activity_emit import emit_schedule_created_activity

    session = AsyncMock()
    tenant_id = uuid4()
    recorded = []

    async def fake_record(sess, topic, envelope, *, tenant_id=None):
        recorded.append((topic, envelope))
        return True

    with patch("app.core.activity_emit.record_from_kafka_topic", fake_record):
        await emit_schedule_created_activity(
            session,
            tenant_id=tenant_id,
            mo_count=2,
            schedule={"solver_status": "OPTIMAL", "assignments": [{}, {}]},
        )

    assert len(recorded) == 1
    assert recorded[0][0] == "ipe.schedule.created"
    assert recorded[0][1]["payload"]["mo_count"] == 2


@pytest.mark.asyncio
async def test_emit_schedule_swallows_errors():
    from app.core.activity_emit import emit_schedule_created_activity

    session = AsyncMock()

    async def boom(*_a, **_k):
        raise RuntimeError("db down")

    with patch("app.core.activity_emit.record_from_kafka_topic", boom):
        await emit_schedule_created_activity(
            session,
            tenant_id=uuid4(),
            mo_count=1,
            schedule={"solver_status": "FEASIBLE", "assignments": []},
        )
