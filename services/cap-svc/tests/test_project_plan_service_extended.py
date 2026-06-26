"""Extended project plan service tests — R2-01."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.project_plan_service import (
    ProjectPlanServiceError,
    activate_version,
    get_active_schedule,
    list_versions,
    operations_to_gantt,
    upload_plan_version,
)


def _parsed(plan_code: str = "PLAN-A") -> dict:
    return {
        "plan_code": plan_code,
        "plan_name": "Demo Plan",
        "file_sha256": "abc123",
        "file_size_bytes": 1024,
        "row_count": 1,
        "operations": [
            {
                "plan_code": plan_code,
                "mo_id": "MO-1",
                "operation_sequence": 10,
                "work_center_code": "WC1",
                "start_minute": 0,
                "end_minute": 120,
                "duration_minutes": 120,
                "status": "frozen",
            }
        ],
    }


def test_operations_to_gantt_groups_by_mo():
    version = MagicMock()
    version.version_number = 2
    version.id = uuid4()
    version.operations = _parsed()["operations"]
    gantt = operations_to_gantt(version)
    assert gantt["plan_code"] == "PLAN-A"
    assert len(gantt["rows"]) == 1
    assert gantt["rows"][0]["operations"][0]["is_frozen"] is True


@pytest.mark.asyncio
async def test_list_versions_not_found():
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    with pytest.raises(ProjectPlanServiceError) as exc:
        await list_versions(session, uuid4(), "MISSING")
    assert exc.value.code == "NOT_FOUND"


@pytest.mark.asyncio
async def test_upload_plan_new_when_exists_raises():
    existing = MagicMock(plan_code="PLAN-A")
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=existing)))
    with pytest.raises(ProjectPlanServiceError) as exc:
        await upload_plan_version(session, uuid4(), uuid4(), _parsed(), "f.xlsx", mode="new")
    assert exc.value.code == "PLAN_EXISTS"


@pytest.mark.asyncio
async def test_upload_plan_update_when_missing_raises():
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    with pytest.raises(ProjectPlanServiceError) as exc:
        await upload_plan_version(session, uuid4(), uuid4(), _parsed(), "f.xlsx", mode="update")
    assert exc.value.code == "PLAN_NOT_FOUND"


@pytest.mark.asyncio
async def test_upload_plan_new_success():
    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
            MagicMock(),
        ]
    )
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    result = await upload_plan_version(session, uuid4(), uuid4(), _parsed(), "plan.xlsx", mode="new")
    assert "version 1" in result["message"]
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_activate_version_success():
    plan = MagicMock()
    plan.plan_code = "PLAN-A"
    plan.id = uuid4()
    version = MagicMock()
    version.version_number = 2
    version.id = uuid4()

    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=plan)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=version)),
            MagicMock(),
        ]
    )
    session.commit = AsyncMock()

    result = await activate_version(session, uuid4(), "PLAN-A", version.id)
    assert "Activated version 2" in result["message"]


@pytest.mark.asyncio
async def test_get_active_schedule_not_found():
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    with pytest.raises(ProjectPlanServiceError):
        await get_active_schedule(session, uuid4(), "PLAN-X")
