"""Unit tests for Sprint 7 EIB activity normalization."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ipe_shared.activity.emit import record_from_kafka_topic
from ipe_shared.events.eib import (
    ACTIVITY_UNIFIED_TOPIC,
    EIB_INGRESS_TOPICS,
    build_summary,
    normalize_kafka_message,
    parse_kafka_topic,
)


def test_parse_kafka_topic():
    tool, event = parse_kafka_topic("ipe.feasibility.scored")
    assert tool == "feasibility"
    assert event == "scored"


def test_normalize_demand_created():
    envelope = {
        "tenant_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        "event_id": "evt-1",
        "payload": {"mo_id": "d1eebc99-9c0b-4ef8-bb6d-6bb9bd380001", "entity": "manufacturing_orders"},
    }
    row = normalize_kafka_message("ipe.demand.created", envelope)
    assert row["source_tool"] == "demand"
    assert row["event_type"] == "created"
    assert "MO" in row["summary"]
    assert row["tenant_id"] == envelope["tenant_id"]


def test_build_summary_custom():
    assert build_summary("connector", "sync_completed", {"summary": "Synced 70 products"}) == "Synced 70 products"


def test_eib_constants():
    assert ACTIVITY_UNIFIED_TOPIC == "ipe.activity.unified"
    assert "ipe.sync.completed" in EIB_INGRESS_TOPICS


@pytest.mark.asyncio
async def test_record_from_kafka_topic_persists(monkeypatch):
    session = AsyncMock()
    recorded = {}

    async def fake_record(session, **kwargs):
        recorded.update(kwargs)
        row = MagicMock()
        row.id = uuid4()
        return row

    monkeypatch.setattr(
        "ipe_shared.activity.emit.record_activity_event",
        fake_record,
    )
    tenant_id = str(uuid4())
    envelope = {
        "tenant_id": tenant_id,
        "event_id": "evt-emit-1",
        "payload": {"mo_id": str(uuid4()), "feasibility_score": 88},
    }
    ok = await record_from_kafka_topic(session, "ipe.feasibility.scored", envelope)
    assert ok is True
    assert recorded["source_tool"] == "feasibility"
    assert recorded["event_type"] == "scored"
