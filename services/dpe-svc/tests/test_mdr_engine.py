from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest

from app.core.mdr_engine import (
    BOM_COMPLETENESS_THRESHOLD,
    LEAD_TIME_ACCURACY_THRESHOLD,
    build_remediation,
    calculate_mdr,
)


@pytest.fixture
def session():
    s = AsyncMock()
    return s


def _setup_mdr_mocks(session, bom_total, bom_with, lt_total, lt_with):
    bom_fetch = MagicMock()
    bom_fetch.fetchone.return_value = (bom_total, bom_with)
    lt_fetch = MagicMock()
    lt_fetch.fetchone.return_value = (lt_total, lt_with)

    async def mock_execute(*args, **kwargs):
        sql = args[0]
        sql_str = str(sql) if hasattr(sql, "compile") else str(sql)
        if "cdm_product" in sql_str and "cdm_bill_of_material" in sql_str:
            return bom_fetch
        if "lead_time_days" in sql_str and "FROM cdm_product" in sql_str:
            return lt_fetch
        return AsyncMock()

    session.execute.side_effect = mock_execute


@pytest.mark.asyncio
async def test_calculate_mdr_all_pass(session):
    _setup_mdr_mocks(session, 10, 9, 20, 17)
    result = await calculate_mdr(session, "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
    assert result["bom_completeness_pct"] == 90.0
    assert result["lead_time_accuracy_pct"] == 85.0
    assert result["passed"] is True


@pytest.mark.asyncio
async def test_calculate_mdr_bom_fails(session):
    _setup_mdr_mocks(session, 10, 6, 20, 17)
    result = await calculate_mdr(session, "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
    assert result["bom_completeness_pct"] == 60.0
    assert result["lead_time_accuracy_pct"] == 85.0
    assert result["passed"] is False


@pytest.mark.asyncio
async def test_calculate_mdr_lead_time_fails(session):
    _setup_mdr_mocks(session, 10, 9, 20, 11)
    result = await calculate_mdr(session, "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
    assert result["bom_completeness_pct"] == 90.0
    assert result["lead_time_accuracy_pct"] == 55.0
    assert result["passed"] is False


@pytest.mark.asyncio
async def test_calculate_mdr_both_fail(session):
    _setup_mdr_mocks(session, 10, 6, 20, 8)
    result = await calculate_mdr(session, "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
    assert result["passed"] is False


@pytest.mark.asyncio
async def test_calculate_mdr_empty_db(session):
    _setup_mdr_mocks(session, 0, 0, 0, 0)
    result = await calculate_mdr(session, "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
    assert result["bom_completeness_pct"] == 0.0
    assert result["lead_time_accuracy_pct"] == 0.0
    assert result["passed"] is False


def test_build_remediation_both():
    mdr = {"bom_completeness_pct": 60.0, "lead_time_accuracy_pct": 40.0}
    steps = build_remediation(mdr)
    assert len(steps) == 2
    assert "BOMs" in steps[0]
    assert "lead time" in steps[1]


def test_build_remediation_bom_only():
    mdr = {"bom_completeness_pct": 60.0, "lead_time_accuracy_pct": 85.0}
    steps = build_remediation(mdr)
    assert len(steps) == 1
    assert "BOMs" in steps[0]


def test_build_remediation_lead_time_only():
    mdr = {"bom_completeness_pct": 90.0, "lead_time_accuracy_pct": 40.0}
    steps = build_remediation(mdr)
    assert len(steps) == 1
    assert "lead time" in steps[0]


def test_build_remediation_none():
    mdr = {"bom_completeness_pct": 90.0, "lead_time_accuracy_pct": 85.0}
    steps = build_remediation(mdr)
    assert len(steps) == 0


def test_thresholds():
    assert BOM_COMPLETENESS_THRESHOLD == 80.0
    assert LEAD_TIME_ACCURACY_THRESHOLD == 60.0
