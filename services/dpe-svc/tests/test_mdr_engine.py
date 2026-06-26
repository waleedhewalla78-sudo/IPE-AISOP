"""MDR engine tests — R2-05 (auth/mdr live in dpe-svc)."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.mdr_engine import calculate_mdr


@pytest.mark.asyncio
async def test_calculate_mdr_no_tenant():
    session = AsyncMock()
    result = await calculate_mdr(session, tenant_id=None)
    assert result["passed"] is False
    assert result["error"] == "No tenant context"


@pytest.mark.asyncio
async def test_calculate_mdr_composite_scores():
    tid = str(uuid4())
    session = AsyncMock()
    session.commit = AsyncMock()

    idx = 0
    metrics = [(10.0, 9.0), (20.0, 18.0), (5.0, 5.0), (8.0, 7.0)]

    async def execute(*args, **kwargs):
        nonlocal idx
        idx += 1
        if idx == 1:
            return MagicMock()
        if idx <= 5:
            return MagicMock(fetchone=MagicMock(return_value=metrics[idx - 2]))
        return MagicMock()

    session.execute = AsyncMock(side_effect=execute)

    result = await calculate_mdr(session, tenant_id=tid)

    assert result["bom_completeness_pct"] == 90.0
    assert result["lead_time_accuracy_pct"] == 90.0
    assert "composite_score" in result
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_calculate_mdr_failing_remediation():
    tid = str(uuid4())
    session = AsyncMock()
    session.commit = AsyncMock()

    idx = 0
    metrics = [(10.0, 5.0), (20.0, 8.0), (5.0, 2.0), (8.0, 3.0)]

    async def execute(*args, **kwargs):
        nonlocal idx
        idx += 1
        if idx == 1:
            return MagicMock()
        if idx <= 5:
            return MagicMock(fetchone=MagicMock(return_value=metrics[idx - 2]))
        return MagicMock()

    session.execute = AsyncMock(side_effect=execute)

    result = await calculate_mdr(session, tenant_id=tid)

    assert result["passed"] is False
    assert result["ai_scheduling_allowed"] is False
    assert len(result["remediation"]) >= 1
