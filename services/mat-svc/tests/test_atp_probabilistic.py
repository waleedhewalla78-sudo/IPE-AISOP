from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from uuid import UUID

import pytest

from app.core.atp import _component_monte_carlo, _sample_delay, probabilistic_atp


class TestSampleDelay:
    def test_normal_distribution(self):
        samples = [_sample_delay("normal", 5.0, 1.0) for _ in range(100)]
        assert all(s >= 0 for s in samples)
        avg = sum(samples) / len(samples)
        assert 2.0 < avg < 8.0

    def test_lognormal_distribution(self):
        samples = [_sample_delay("lognormal", 5.0, 2.0) for _ in range(100)]
        assert all(s >= 0 for s in samples)
        avg = sum(samples) / len(samples)
        assert avg > 0

    def test_lognormal_zero_mean_returns_zero(self):
        assert _sample_delay("lognormal", 0.0, 1.0) == 0.0


class TestComponentMonteCarlo:
    def test_available_now_returns_high_confidence(self):
        result = _component_monte_carlo(
            on_hand=100, reserved=0, supply_orders=[],
            required_qty=50, required_date=datetime(2026, 7, 1, tzinfo=UTC),
            priority_demand=0, num_simulations=100,
        )
        assert result["is_available_now"] is True
        assert result["confidence"] >= 0.9

    def test_shortage_returns_low_confidence(self):
        result = _component_monte_carlo(
            on_hand=10, reserved=5, supply_orders=[],
            required_qty=100, required_date=datetime(2026, 7, 1, tzinfo=UTC),
            priority_demand=0, num_simulations=100,
        )
        assert result["is_available_now"] is False
        assert result["confidence"] == 0.0


@pytest.mark.asyncio
async def test_probabilistic_atp_returns_expected_structure():
    mock_get_inventory = AsyncMock(
        return_value={"qty_on_hand": 100, "qty_reserved": 10, "qty_in_transit": 0}
    )
    mock_get_open_supply = AsyncMock(return_value=[
        {
            "id": "sup-1",
            "quantity_ordered": 200,
            "quantity_received": 0,
            "expected_date": "2026-06-25T00:00:00+00:00",
            "adjusted_date": "2026-06-27T00:00:00+00:00",
            "status": "confirmed",
            "supplier_name": "Supplier A",
            "expected_delay_days": 2.0,
            "delay_std_dev": 0.5,
            "confidence": 0.9,
        },
    ])

    comp_a = str(UUID(int=100))
    comp_b = str(UUID(int=101))

    with patch("app.core.atp.get_current_inventory", mock_get_inventory), \
         patch("app.core.atp.get_open_supply", mock_get_open_supply):
        result = await probabilistic_atp(
            session=AsyncMock(),
            tenant_id=UUID(int=1),
            mo={"id": "MO-001", "mo_number": "MO-001", "quantity": 10},
            components=[
                {"component_id": comp_a, "quantity_per": 2},
                {"component_id": comp_b, "quantity_per": 1},
            ],
            priority_queue=[],
            required_start=datetime(2026, 7, 1, tzinfo=UTC),
            num_simulations=100,
        )

    assert result["mo_id"] == "MO-001"
    assert result["mo_number"] == "MO-001"
    assert "component_breakdown" in result
    assert len(result["component_breakdown"]) == 2
    assert "bottleneck_component_id" in result
    assert "overall_confidence" in result
    assert 0 <= result["overall_confidence"] <= 1
