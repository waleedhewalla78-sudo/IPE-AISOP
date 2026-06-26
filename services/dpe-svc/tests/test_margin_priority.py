"""Unit tests for margin-aware priority computation."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.margin_priority import (
    MarginPriorityResult,
    compute_margin_adjusted_priority,
    compute_margin_priorities_for_mos,
)


@pytest.mark.asyncio
async def test_missing_cost_driver_falls_back_to_base():
    session = AsyncMock()
    tenant_id = uuid4()
    mo_id = uuid4()
    product_id = uuid4()

    mo = MagicMock()
    mo.id = mo_id
    mo.product_id = product_id
    mo.bom_id = uuid4()
    mo.quantity = 10
    mo.feasibility_score = 72

    demand_result = MagicMock()
    demand_result.scalar.return_value = 72.0

    product = MagicMock()
    product.standard_cost = 10.0

    product_result = MagicMock()
    product_result.scalar_one_or_none.return_value = product

    driver_result = MagicMock()
    driver_result.scalar_one_or_none.return_value = None

    session.execute = AsyncMock(side_effect=[demand_result, product_result, driver_result])

    result = await compute_margin_adjusted_priority(session, tenant_id, mo)
    assert result.base_priority_score == 72.0
    assert result.margin_adjusted_score == 72.0
    assert result.warning == "MISSING_COST_DRIVER"
    assert result.data_quality == "missing_cost_driver"


@pytest.mark.asyncio
async def test_compute_margin_priorities_collects_warnings():
    session = AsyncMock()
    tenant_id = uuid4()
    mo = MagicMock()
    mo.id = uuid4()
    mo.product_id = uuid4()
    mo.bom_id = uuid4()
    mo.quantity = 5
    mo.feasibility_score = 60

    mo_result = MagicMock()
    mo_result.scalars.return_value.all.return_value = [mo]

    demand_result = MagicMock()
    demand_result.scalar.return_value = None

    product = MagicMock()
    product.standard_cost = 10.0

    product_result = MagicMock()
    product_result.scalar_one_or_none.return_value = product

    driver_result = MagicMock()
    driver_result.scalar_one_or_none.return_value = None

    session.execute = AsyncMock(side_effect=[mo_result, demand_result, product_result, driver_result])

    priorities, warnings = await compute_margin_priorities_for_mos(session, tenant_id)
    assert len(priorities) == 1
    assert len(warnings) == 1
    assert warnings[0]["code"] == "MISSING_COST_DRIVER"


def test_margin_priority_result_dataclass():
    item = MarginPriorityResult(
        mo_id="abc",
        base_priority_score=50.0,
        margin_adjusted_score=65.0,
        net_margin_usd=100.0,
        activity_overhead_usd=20.0,
        data_quality="complete",
    )
    assert item.margin_adjusted_score >= item.base_priority_score


@pytest.mark.asyncio
async def test_margin_adjusted_priority_complete_path():
    session = AsyncMock()
    tenant_id = uuid4()
    mo = MagicMock()
    mo.id = uuid4()
    mo.product_id = uuid4()
    mo.bom_id = uuid4()
    mo.quantity = 10
    mo.feasibility_score = 60

    driver = MagicMock(
        setup_mins=20,
        overtime_rate_usd_per_hr=40,
        overhead_pct=0.05,
        expedite_cost_per_unit=2,
    )
    product = MagicMock(standard_cost=50.0)
    routing = MagicMock()

    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar=MagicMock(return_value=None)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=product)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=driver)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[routing])))),
        ]
    )

    result = await compute_margin_adjusted_priority(session, tenant_id, mo)
    assert result.data_quality == "complete"
    assert result.warning is None
    assert result.net_margin_usd != 0


def test_normalize_margin_to_score_zero_max():
    from app.core.margin_priority import _normalize_margin_to_score

    assert _normalize_margin_to_score(100, 0) == 50.0
