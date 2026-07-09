"""Sprint 7 T717 — connector activity emit on Odoo sync."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from ipe_shared.events.eib import normalize_kafka_message


def test_sync_completed_topic_parses():
    tool, event = __import__(
        "ipe_shared.events.eib", fromlist=["parse_kafka_topic"]
    ).parse_kafka_topic("ipe.sync.completed")
    assert tool == "sync"
    assert event == "completed"


def test_sync_activity_summary_from_payload():
    from ipe_shared.events.eib import build_summary

    summary = build_summary(
        "sync",
        "completed",
        {"summary": "Odoo sync success: products updated=70 MOs updated=2"},
    )
    assert "70" in summary


def test_normalize_sync_envelope():
    tenant_id = str(uuid4())
    envelope = {
        "tenant_id": tenant_id,
        "event_id": "sync-1",
        "payload": {
            "summary": "Odoo sync success",
            "status": "success",
            "sync_run_id": str(uuid4()),
        },
    }
    row = normalize_kafka_message("ipe.sync.completed", envelope)
    assert row["source_tool"] == "sync"
    assert row["event_type"] == "completed"
    assert row["tenant_id"] == tenant_id


@pytest.mark.asyncio
async def test_run_full_sync_emits_on_success():
    from app.odoo.sync_engine import OdooSyncEngine

    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()

    engine = OdooSyncEngine(MagicMock(), uuid4(), session)
    emitted = []

    async def fake_emit(sess, topic, envelope, *, tenant_id=None):
        emitted.append((topic, envelope))
        return True

    with patch.object(OdooSyncEngine, "sync_products", AsyncMock(return_value={"updated": 1, "errors": 0})):
        with patch.object(OdooSyncEngine, "sync_work_centers", AsyncMock(return_value={"updated": 0, "errors": 0})):
            with patch.object(OdooSyncEngine, "sync_customers", AsyncMock(return_value={"updated": 0, "errors": 0})):
                with patch.object(OdooSyncEngine, "sync_suppliers", AsyncMock(return_value={"updated": 0, "errors": 0})):
                    with patch.object(OdooSyncEngine, "sync_boms", AsyncMock(return_value={"updated": 0, "errors": 0})):
                        with patch.object(
                            OdooSyncEngine, "sync_bom_details", AsyncMock(return_value={"updated": 0, "errors": 0})
                        ):
                            with patch.object(
                                OdooSyncEngine, "sync_inventory", AsyncMock(return_value={"updated": 0, "errors": 0})
                            ):
                                with patch.object(
                                    OdooSyncEngine,
                                    "sync_manufacturing_orders",
                                    AsyncMock(return_value={"updated": 2, "errors": 0}),
                                ):
                                    with patch.object(
                                        OdooSyncEngine, "sync_demands", AsyncMock(return_value={"updated": 0, "errors": 0})
                                    ):
                                        with patch.object(
                                            OdooSyncEngine, "sync_supply", AsyncMock(return_value={"updated": 0, "errors": 0})
                                        ):
                                            with patch.object(
                                                OdooSyncEngine, "_rescore_synced_mos", AsyncMock(return_value=0)
                                            ):
                                                with patch(
                                                    "app.odoo.sync_engine.record_from_kafka_topic",
                                                    fake_emit,
                                                ):
                                                    result = await engine.run_full_sync(trigger="test")

    assert result["status"] == "success"
    assert len(emitted) == 1
    assert emitted[0][0] == "ipe.sync.completed"


@pytest.mark.asyncio
async def test_run_full_sync_skips_emit_on_failure():
    from app.odoo.sync_engine import OdooSyncEngine

    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()

    engine = OdooSyncEngine(MagicMock(), uuid4(), session)
    emitted = []

    async def fake_emit(*_a, **_k):
        emitted.append(True)
        return True

    with patch.object(OdooSyncEngine, "sync_products", AsyncMock(side_effect=RuntimeError("odoo down"))):
        with patch("app.odoo.sync_engine.record_from_kafka_topic", fake_emit):
            with pytest.raises(RuntimeError):
                await engine.run_full_sync(trigger="test")

    assert emitted == []
