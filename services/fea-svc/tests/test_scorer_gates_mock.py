"""Async capacity/labor gate tests with mocked DB (P8 R1-02)."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.scorer import _compute_capacity_gate, _compute_labor_gate


@pytest.mark.asyncio
async def test_capacity_gate_no_work_centers():
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(fetchall=MagicMock(return_value=[])))
    score = await _compute_capacity_gate(str(uuid4()), str(uuid4()), session)
    assert score == 100.0


@pytest.mark.asyncio
async def test_capacity_gate_with_utilization():
    wc_id = uuid4()
    session = AsyncMock()

    def execute_side_effect(stmt, params=None):
        sql = str(stmt)
        if "routing_operation" in sql:
            return MagicMock(fetchall=MagicMock(return_value=[(wc_id,)]))
        if "SUM(wo.duration" in sql:
            return MagicMock(scalar=MagicMock(return_value=600.0))
        if "cdm_work_center" in sql:
            return MagicMock(one_or_none=MagicMock(return_value=(8.0, 0.85)))
        return MagicMock()

    session.execute = AsyncMock(side_effect=execute_side_effect)
    score = await _compute_capacity_gate(str(uuid4()), str(uuid4()), session)
    assert 0 <= score <= 100


@pytest.mark.asyncio
async def test_labor_gate_with_headcount():
    wc_id = uuid4()
    session = AsyncMock()

    def execute_side_effect(stmt, params=None):
        sql = str(stmt)
        if "routing_operation" in sql:
            return MagicMock(fetchall=MagicMock(return_value=[(wc_id,)]))
        if "headcount" in sql or "labor" in sql.lower():
            return MagicMock(one_or_none=MagicMock(return_value=(5, 8)))
        if "SUM(wo.duration" in sql:
            return MagicMock(scalar=MagicMock(return_value=120.0))
        return MagicMock(fetchall=MagicMock(return_value=[]))

    session.execute = AsyncMock(side_effect=execute_side_effect)
    score = await _compute_labor_gate(str(uuid4()), str(uuid4()), session)
    assert 0 <= score <= 100


@pytest.mark.asyncio
async def test_labor_gate_no_work_centers():
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(fetchall=MagicMock(return_value=[])))
    score = await _compute_labor_gate(str(uuid4()), str(uuid4()), session)
    assert score == 100.0
