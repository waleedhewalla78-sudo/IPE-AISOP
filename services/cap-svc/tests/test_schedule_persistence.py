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


def test_schedule_persistence_error_attributes():
    err = SchedulePersistenceError("VERSION_CONFLICT", "stale version")
    assert err.code == "VERSION_CONFLICT"
    assert "stale" in err.message
