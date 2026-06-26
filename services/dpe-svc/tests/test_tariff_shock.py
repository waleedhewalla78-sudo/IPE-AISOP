"""Unit tests for tariff shock simulation."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.tariff_shock import (
    TariffExposureRow,
    _estimate_tariff_cost_delta,
    get_tariff_exposure,
    run_tariff_shock,
)
from ipe_shared.models.landed_cost import LandedCostProfile
from ipe_shared.models.material_attributes import MaterialAttribute


def test_estimate_tariff_cost_delta():
    profile = LandedCostProfile(base_cost_usd=Decimal("10"))
    delta = _estimate_tariff_cost_delta(profile, mo_qty=100, bom_qty_per=2.0, tariff_delta_pct=25.0)
    assert delta == 500.0


@pytest.mark.asyncio
async def test_get_tariff_exposure_empty():
    session = AsyncMock()
    empty = MagicMock()
    empty.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=empty)

    rows = await get_tariff_exposure(session, uuid4())
    assert rows == []


@pytest.mark.asyncio
async def test_get_tariff_exposure_with_region_data(monkeypatch):
    session = AsyncMock()
    tenant_id = uuid4()
    mat_id = uuid4()
    bom_id = uuid4()

    attr = MagicMock(spec=MaterialAttribute)
    attr.material_id = mat_id
    attr.attributes = {"origin_region": "US"}

    attr_result = MagicMock()
    attr_result.scalars.return_value.all.return_value = [attr]

    profile = LandedCostProfile(
        region="US",
        base_cost_usd=Decimal("100"),
        freight_usd=Decimal("0"),
        tariff_pct=Decimal("10"),
        risk_premium_pct=Decimal("0"),
    )
    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile

    mo = MagicMock()
    mo.bom_id = bom_id
    mo.quantity = 5

    bom_line = MagicMock()
    bom_line.quantity_per = 2.0
    bom_result = MagicMock()
    bom_result.scalars.return_value.all.return_value = [bom_line]

    async def fake_mos(*args, **kwargs):
        return [mo]

    monkeypatch.setattr("app.core.tariff_shock._mos_using_materials", fake_mos)
    session.execute = AsyncMock(side_effect=[attr_result, profile_result, bom_result])

    rows = await get_tariff_exposure(session, tenant_id)
    assert len(rows) == 1
    assert rows[0].region == "US"
    assert rows[0].material_count == 1
    assert rows[0].mo_count == 1
    assert rows[0].total_exposure_usd == 100.0


@pytest.mark.asyncio
async def test_get_tariff_exposure_skips_attrs_without_region():
    session = AsyncMock()
    attr = MagicMock(spec=MaterialAttribute)
    attr.material_id = uuid4()
    attr.attributes = {}

    attr_result = MagicMock()
    attr_result.scalars.return_value.all.return_value = [attr]
    session.execute = AsyncMock(return_value=attr_result)

    rows = await get_tariff_exposure(session, uuid4())
    assert rows == []


@pytest.mark.asyncio
async def test_run_tariff_shock_flags_mos_and_substitutes(monkeypatch):
    session = AsyncMock()
    tenant_id = uuid4()
    mo_id = uuid4()
    mat_id = uuid4()
    sub_id = uuid4()

    mo = MagicMock()
    mo.id = mo_id
    mo.bom_id = uuid4()
    mo.product_id = uuid4()
    mo.quantity = 100

    product = MagicMock()
    product.standard_cost = 10.0

    profile = LandedCostProfile(
        region="Region_X",
        base_cost_usd=Decimal("10"),
        freight_usd=Decimal("0"),
        tariff_pct=Decimal("20"),
        risk_premium_pct=Decimal("0"),
    )

    bom_line = MagicMock()
    bom_line.component_id = mat_id
    bom_line.quantity_per = 2.0

    async def fake_materials(*args, **kwargs):
        return [mat_id]

    async def fake_mos(*args, **kwargs):
        return [mo]

    async def fake_substitute_map(*args, **kwargs):
        return {str(mat_id): str(sub_id)}

    async def fake_margin(*args, **kwargs):
        from app.core.margin_priority import MarginPriorityResult

        return MarginPriorityResult(
            mo_id=str(mo_id),
            base_priority_score=50.0,
            margin_adjusted_score=50.0,
            net_margin_usd=500.0,
            activity_overhead_usd=100.0,
            data_quality="complete",
        )

    monkeypatch.setattr("app.core.tariff_shock._materials_in_region", fake_materials)
    monkeypatch.setattr("app.core.tariff_shock._mos_using_materials", fake_mos)
    monkeypatch.setattr("app.core.tariff_shock._get_substitute_map", fake_substitute_map)
    monkeypatch.setattr("app.core.tariff_shock.compute_margin_adjusted_priority", fake_margin)

    profile_result = MagicMock()
    profile_result.scalar_one_or_none.return_value = profile
    bom_result = MagicMock()
    bom_result.scalars.return_value.all.return_value = [bom_line]
    product_result = MagicMock()
    product_result.scalar_one_or_none.return_value = product
    session.execute = AsyncMock(side_effect=[profile_result, bom_result, product_result])

    result = await run_tariff_shock(
        session,
        tenant_id,
        region="Region_X",
        tariff_delta_pct=25.0,
        margin_threshold_pct=15.0,
    )
    assert result["affected_mo_count"] == 1
    assert len(result["mos_below_threshold"]) == 1
    assert result["substitute_drafts"][0]["to_material_id"] == str(sub_id)
