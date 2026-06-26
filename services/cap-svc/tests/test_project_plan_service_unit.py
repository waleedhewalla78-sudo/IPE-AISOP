"""Project plan service unit tests — R2-01."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.project_plan_service import ProjectPlanServiceError, get_plan_by_code, list_plans


@pytest.mark.asyncio
async def test_get_plan_by_code_none():
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    plan = await get_plan_by_code(session, uuid4(), "MISSING")
    assert plan is None


@pytest.mark.asyncio
async def test_list_plans_empty():
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))
    plans = await list_plans(session, uuid4())
    assert plans == []


def test_service_error_attributes():
    err = ProjectPlanServiceError("NOT_FOUND", "missing plan")
    assert err.code == "NOT_FOUND"
    assert "missing" in str(err)
