"""Unit tests for schedule persistence core logic."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.schedule_persistence import (
    SchedulePersistenceError,
    approve_schedule_mos,
    load_active_schedule,
    persist_schedule_proposal,
)


@pytest.mark.asyncio
async def test_persist_schedule_proposal_empty():
    session = AsyncMock()
    result = await persist_schedule_proposal(session, uuid4(), [])
    assert result == {"updated_mos": 0, "updated_work_orders": 0}
    session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_persist_schedule_proposal_skips_synthetic_maintenance_ops():
    session = AsyncMock()
    mo_id = uuid4()
    op_id = uuid4()
    wc_id = uuid4()
    tenant_id = uuid4()

    mo_result = MagicMock()
    mo = MagicMock()
    mo_result.scalar_one_or_none.return_value = mo
    wo_result = MagicMock()
    wo_result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(side_effect=[wo_result, mo_result])
    session.flush = AsyncMock()
    session.commit = AsyncMock()

    assignments = [
        {
            "mo_id": f"MAINT_WC002",
            "operation_id": "MAINT_WC002_abc12345",
            "work_center_id": str(wc_id),
            "start_minute": 0,
            "end_minute": 60,
            "duration": 60,
            "sequence": 0,
        },
        {
            "mo_id": str(mo_id),
            "operation_id": str(op_id),
            "work_center_id": str(wc_id),
            "start_minute": 0,
            "end_minute": 60,
            "duration": 60,
            "sequence": 1,
        },
    ]
    result = await persist_schedule_proposal(session, tenant_id, assignments)
    assert result["updated_work_orders"] == 1
    session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_approve_schedule_mos_not_found():
    session = AsyncMock()
    mo_id = uuid4()
    tenant_id = uuid4()

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result_mock)

    result = await approve_schedule_mos(session, tenant_id, [mo_id])
    assert result["activated_count"] == 0
    assert result["failed_count"] == 1
    assert result["failed"][0]["reason"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_approve_schedule_mos_version_conflict():
    session = AsyncMock()
    mo_id = uuid4()
    tenant_id = uuid4()

    mo = MagicMock()
    mo.version = 2
    mo.ai_suggested_start = datetime.now(UTC)
    mo.ai_suggested_end = datetime.now(UTC)

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = mo
    session.execute = AsyncMock(return_value=result_mock)

    result = await approve_schedule_mos(
        session,
        tenant_id,
        [mo_id],
        expected_versions={str(mo_id): 1},
    )
    assert result["failed_count"] == 1
    assert result["failed"][0]["reason"] == "VERSION_CONFLICT"


@pytest.mark.asyncio
async def test_load_active_schedule_empty():
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.all.return_value = []
    session.execute = AsyncMock(return_value=result_mock)

    rows = await load_active_schedule(session, uuid4())
    assert rows == []


@pytest.mark.asyncio
async def test_approve_schedule_mos_kafka_publish_failure():
    """CDM commit succeeds but API must surface ERP sync failure when Kafka is down."""
    from unittest.mock import patch

    session = AsyncMock()
    mo_id = uuid4()
    tenant_id = uuid4()

    mo = MagicMock()
    mo.version = 1
    mo.feasibility_score = 90.0
    mo.ai_suggested_start = datetime.now(UTC)
    mo.ai_suggested_end = datetime.now(UTC)
    mo.planned_start = None
    mo.planned_end = None
    mo.ai_schedule_version = 0
    mo.status = "draft"
    mo.erp_mo_id = "MO-001"
    mo.updated_at = None

    mo_result = MagicMock()
    mo_result.scalar_one_or_none.return_value = mo
    wo_result = MagicMock()
    wo_result.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(side_effect=[mo_result, wo_result])

    with patch(
        "app.core.schedule_persistence.kafka_producer.send_avro",
        new_callable=AsyncMock,
        side_effect=RuntimeError("kafka unavailable"),
    ):
        result = await approve_schedule_mos(session, tenant_id, [mo_id])

    session.commit.assert_called_once()
    assert result["activated_count"] == 1
    assert result["erp_event_published"] is False


def test_schedule_persistence_error_attributes():
    err = SchedulePersistenceError("VERSION_CONFLICT", "stale version")
    assert err.code == "VERSION_CONFLICT"
    assert "stale" in err.message
