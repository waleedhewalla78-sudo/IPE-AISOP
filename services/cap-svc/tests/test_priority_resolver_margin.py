"""Margin-aware priority full path — R2-01."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.priority_resolver import resolve_mo_priority_margin_aware


@pytest.mark.asyncio
async def test_resolve_mo_priority_margin_aware_with_driver():
    mo = MagicMock(
        id=uuid4(),
        product_id=uuid4(),
        feasibility_score=80.0,
        quantity=10,
        bom_id=uuid4(),
    )
    driver = MagicMock(setup_mins=30, overtime_rate_usd_per_hr=50, overhead_pct=0.1, expedite_cost_per_unit=5)
    product = MagicMock(standard_cost=100.0)
    routing = MagicMock()

    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar=MagicMock(return_value=None)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=driver)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=product)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[routing, routing])))),
        ]
    )

    weight, warning = await resolve_mo_priority_margin_aware(session, uuid4(), mo)
    assert warning is None
    assert 0.01 <= weight <= 1.0
