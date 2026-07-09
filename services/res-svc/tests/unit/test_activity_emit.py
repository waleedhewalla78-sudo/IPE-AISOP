"""Sprint 7 T719 — res-svc activity emit on resolution approved."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from ipe_shared.events.eib import build_summary, normalize_kafka_message


def test_resolution_approved_topic_parses():
    from ipe_shared.events.eib import parse_kafka_topic

    tool, event = parse_kafka_topic("ipe.resolution.approved")
    assert tool == "resolution"
    assert event == "approved"


def test_resolution_summary_from_strategy():
    summary = build_summary(
        "resolution",
        "approved",
        {"summary": "Resolution approved: expedite for MO-ST-001"},
    )
    assert "expedite" in summary


def test_normalize_resolution_envelope():
    tenant_id = str(uuid4())
    mo_id = str(uuid4())
    envelope = {
        "tenant_id": tenant_id,
        "event_id": "res-1",
        "payload": {
            "scenario_id": str(uuid4()),
            "mo_id": mo_id,
            "strategy": "expedite",
            "approved_by": "planner@startrans",
        },
    }
    row = normalize_kafka_message("ipe.resolution.approved", envelope)
    assert row["source_tool"] == "resolution"
    assert row["event_type"] == "approved"
    assert row["entity_id"] == mo_id


@pytest.mark.asyncio
async def test_record_from_kafka_topic_resolution_approved():
    from ipe_shared.activity.emit import record_from_kafka_topic

    session = AsyncMock()
    tenant_id = str(uuid4())
    recorded = {}

    async def fake_record(session, **kwargs):
        recorded.update(kwargs)
        return MagicMock()

    with patch("ipe_shared.activity.emit.record_activity_event", fake_record):
        envelope = {
            "tenant_id": tenant_id,
            "event_id": "evt-res",
            "payload": {"mo_id": str(uuid4()), "strategy": "overtime"},
        }
        ok = await record_from_kafka_topic(
            session, "ipe.resolution.approved", envelope, tenant_id=tenant_id
        )

    assert ok is True
    assert recorded["source_tool"] == "resolution"
    assert recorded["event_type"] == "approved"


@pytest.mark.asyncio
async def test_resolution_envelope_idempotency_key():
    envelope = {
        "tenant_id": str(uuid4()),
        "event_id": "unique-evt-99",
        "payload": {"mo_id": str(uuid4())},
    }
    row = normalize_kafka_message("ipe.resolution.approved", envelope)
    assert row["idempotency_key"] == "unique-evt-99"
