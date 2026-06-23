import random
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.atp import _component_monte_carlo, _sample_delay, compute_material_score


class TestSampleDelay:
    def test_normal_delay_non_negative(self):
        for _ in range(100):
            d = _sample_delay("normal", 5.0, 2.0)
            assert d >= 0

    def test_lognormal_delay_non_negative(self):
        for _ in range(100):
            d = _sample_delay("lognormal", 3.0, 1.5)
            assert d >= 0

    def test_lognormal_zero_mean_returns_zero(self):
        d = _sample_delay("lognormal", 0.0, 1.0)
        assert d == 0.0


class TestComponentMonteCarlo:
    def test_non_degenerate_probability(self):
        random.seed(42)
        supply = [
            {"id": "s1", "quantity_ordered": 100, "quantity_received": 0,
             "expected_date": (datetime.now(UTC) + timedelta(days=10)).isoformat(),
             "distribution_type": "normal", "expected_delay_days": 5.0,
             "delay_std_dev": 3.0},
        ]
        result = _component_monte_carlo(
            on_hand=50, reserved=0, supply_orders=supply,
            required_qty=100, required_date=datetime.now(UTC) + timedelta(days=12),
            priority_demand=0, num_simulations=1000,
        )
        assert 0 <= result["confidence"] <= 1.0

    def test_fallback_path_insufficient_supply(self):
        supply = [
            {"id": "s1", "quantity_ordered": 10, "quantity_received": 0,
             "expected_date": (datetime.now(UTC) + timedelta(days=5)).isoformat(),
             "distribution_type": "normal", "expected_delay_days": 0.5,
             "delay_std_dev": 0.2},
        ]
        result = _component_monte_carlo(
            on_hand=5, reserved=0, supply_orders=supply,
            required_qty=100, required_date=datetime.now(UTC) + timedelta(days=7),
            priority_demand=0, num_simulations=500,
        )
        assert result["confidence"] == 0.0

    def test_deterministic_when_plenty_on_hand(self):
        result = _component_monte_carlo(
            on_hand=1000, reserved=0, supply_orders=[],
            required_qty=100, required_date=datetime.now(UTC) + timedelta(days=1),
            priority_demand=0, num_simulations=100,
        )
        assert result["confidence"] == 1.0


class TestComputeMaterialScore:
    @pytest.mark.asyncio
    async def test_returns_dict_with_expected_keys(self):
        mo_id = uuid4()
        tenant_id = uuid4()
        mock_session = AsyncMock()

        mock_mo = MagicMock()
        mock_mo.bom_id = uuid4()
        mock_mo.quantity = 100
        mock_mo.planned_start = datetime.now(UTC)
        mock_session.execute = AsyncMock()

        with patch("app.core.atp.get_mo_by_id", AsyncMock(return_value=mock_mo)):
            with patch("app.core.atp.get_bom_components", AsyncMock(return_value=[])):
                with patch("app.core.atp.get_current_inventory",
                           AsyncMock(return_value={"qty_on_hand": 0, "qty_reserved": 0})):
                    with patch("app.core.atp.get_open_supply", AsyncMock(return_value=[])):
                        with patch.object(mock_session, "execute", AsyncMock(return_value=MagicMock(
                            scalar_one_or_none=MagicMock(return_value=None)))):
                            result = await compute_material_score(mo_id, tenant_id, mock_session, num_simulations=100)
                            assert "mo_id" in result
                            assert "material_score" in result
