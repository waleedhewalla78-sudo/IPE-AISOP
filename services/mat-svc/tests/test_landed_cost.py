"""Unit tests for landed cost computation."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.landed_cost import _profile_to_breakdown, compute_landed_cost
from ipe_shared.models.landed_cost import LandedCostProfile
from ipe_shared.models.material_attributes import MaterialAttribute


def test_profile_to_breakdown_includes_tariff_and_risk():
    profile = LandedCostProfile(
        base_cost_usd=Decimal("10"),
        freight_usd=Decimal("1.5"),
        tariff_pct=Decimal("20"),
        risk_premium_pct=Decimal("7.5"),
    )
    result = _profile_to_breakdown(profile)
    assert result["landed_cost_per_unit"] == 14.25
    assert result["landed_cost_breakdown"]["tariff_usd"] == 2.0
    assert result["landed_cost_breakdown"]["risk_premium_usd"] == 0.75


def test_profile_to_breakdown_applies_tariff_delta():
    profile = LandedCostProfile(
        base_cost_usd=Decimal("10"),
        freight_usd=Decimal("0"),
        tariff_pct=Decimal("20"),
        risk_premium_pct=Decimal("0"),
    )
    result = _profile_to_breakdown(profile, tariff_delta_pct=25.0)
    assert result["landed_cost_breakdown"]["tariff_usd"] == 4.5


@pytest.mark.asyncio
async def test_compute_landed_cost_from_db():
    session = AsyncMock()
    tenant_id = uuid4()
    material_id = uuid4()

    attr = MaterialAttribute(
        material_id=material_id,
        attributes={
            "origin_region": "Region_X",
            "tariff_code": "HS-8471",
            "carbon_intensity_kg": 12.4,
        },
    )
    profile = LandedCostProfile(
        region="Region_X",
        base_cost_usd=Decimal("10"),
        freight_usd=Decimal("1.5"),
        tariff_pct=Decimal("20"),
        risk_premium_pct=Decimal("7.5"),
    )

    attr_result = MagicMock()
    attr_result.scalar_one_or_none.return_value = attr
    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile
    session.execute = AsyncMock(side_effect=[attr_result, profile_result])

    result = await compute_landed_cost(session, tenant_id, material_id)
    assert result["landed_cost_per_unit"] == 14.25
    assert result["material_attributes"]["tariff_code"] == "HS-8471"
