"""Priority resolver async paths — R2-01."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.priority_resolver import (
    passes_feasibility_guardrail,
    resolve_mo_priority,
    resolve_mo_priority_margin_aware,
)


@pytest.mark.asyncio
async def test_resolve_mo_priority_from_demand():
    mo = MagicMock(id=uuid4(), product_id=uuid4(), feasibility_score=70.0, quantity=10, bom_id=uuid4())
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(scalar=MagicMock(return_value=85.0)))
    weight = await resolve_mo_priority(session, uuid4(), mo)
    assert weight == 0.85


@pytest.mark.asyncio
async def test_resolve_mo_priority_fallback_feasibility():
    mo = MagicMock(id=uuid4(), product_id=uuid4(), feasibility_score=92.0, quantity=5, bom_id=uuid4())
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(scalar=MagicMock(return_value=None)))
    weight = await resolve_mo_priority(session, uuid4(), mo)
    assert weight == 0.92


@pytest.mark.asyncio
async def test_resolve_mo_priority_margin_aware_missing_driver():
    mo = MagicMock(id=uuid4(), product_id=uuid4(), feasibility_score=80.0, quantity=5, bom_id=uuid4())
    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar=MagicMock(return_value=None)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        ]
    )
    weight, warning = await resolve_mo_priority_margin_aware(session, uuid4(), mo)
    assert warning == "MISSING_COST_DRIVER"
    assert weight == 0.8


def test_feasibility_guardrail():
    assert passes_feasibility_guardrail(90.0) is True
    assert passes_feasibility_guardrail(70.0) is False
    assert passes_feasibility_guardrail(None) is True
