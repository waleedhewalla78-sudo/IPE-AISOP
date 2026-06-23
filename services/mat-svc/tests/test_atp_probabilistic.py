from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from uuid import UUID

import pytest

from app.core.atp import (
    _component_monte_carlo,
    _sample_delay,
    probabilistic_atp,
    rule_based_atp,
    simulate_atp,
)


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


class TestSimulateAtp:
    @pytest.mark.asyncio
    async def test_returns_expected_structure(self):
        mock_inv = AsyncMock(
            return_value={"qty_on_hand": 200, "qty_reserved": 10, "qty_in_transit": 50}
        )
        mock_supply = AsyncMock(return_value=[
            {
                "supply_order_id": "SO-1",
                "supplier_id": "SUP-1",
                "quantity_ordered": 100,
                "quantity_received": 0,
                "expected_date": "2026-06-20T00:00:00+00:00",
                "adjusted_date": "2026-06-20T00:00:00+00:00",
            },
        ])
        with patch("app.core.atp.get_current_inventory", mock_inv), \
             patch("app.core.atp.get_open_supply", mock_supply):
            result = await simulate_atp(
                session=AsyncMock(),
                tenant_id=UUID(int=1),
                product_id=UUID(int=10),
                quantity=50,
                required_date=datetime(2026, 7, 1, tzinfo=UTC),
                num_simulations=100,
            )
        assert result["product_id"] == str(UUID(int=10))
        assert result["quantity_requested"] == 50
        assert result["is_available"] is True
        assert 0 <= result["availability_p90"] <= 1
        assert result["available_now"] == 190.0
        assert result["in_transit"] == 50.0
        assert result["supply_arriving_by_date"] == 100.0
        assert result["num_simulations"] == 100

    @pytest.mark.asyncio
    async def test_shortage_returns_low_availability(self):
        mock_inv = AsyncMock(
            return_value={"qty_on_hand": 5, "qty_reserved": 3, "qty_in_transit": 0}
        )
        mock_supply = AsyncMock(return_value=[])
        with patch("app.core.atp.get_current_inventory", mock_inv), \
             patch("app.core.atp.get_open_supply", mock_supply):
            result = await simulate_atp(
                session=AsyncMock(),
                tenant_id=UUID(int=1),
                product_id=UUID(int=10),
                quantity=100,
                required_date=datetime(2026, 7, 1, tzinfo=UTC),
                num_simulations=100,
            )
        assert result["is_available"] is False
        assert result["availability_p90"] == 0.0


class TestRuleBasedAtp:
    @pytest.mark.asyncio
    async def test_available_when_enough_supply_on_time(self):
        mock_inv = AsyncMock(
            return_value={"qty_on_hand": 50, "qty_reserved": 10, "qty_in_transit": 0}
        )
        mock_supply = AsyncMock(return_value=[
            {
                "supply_order_id": "SO-1",
                "supplier_id": "SUP-1",
                "quantity_ordered": 100,
                "quantity_received": 0,
                "expected_date": "2026-06-25T00:00:00+00:00",
            },
        ])
        with patch("app.core.atp.get_current_inventory", mock_inv), \
             patch("app.core.atp.get_open_supply", mock_supply):
            result = await rule_based_atp(
                session=AsyncMock(),
                tenant_id=UUID(int=1),
                product_id=UUID(int=10),
                quantity=80,
                required_date=datetime(2026, 7, 1, tzinfo=UTC),
                delay_buffer_days=1.5,
            )
        assert result["is_available"] is True
        assert result["available_now"] == 40.0
        assert result["shortage"] == 0.0
        assert len(result["supply_contribution_breakdown"]) == 1
        assert result["supply_contribution_breakdown"][0]["arrives_on_time"] is True

    @pytest.mark.asyncio
    async def test_shortage_when_supply_arrives_late(self):
        mock_inv = AsyncMock(
            return_value={"qty_on_hand": 10, "qty_reserved": 0, "qty_in_transit": 0}
        )
        mock_supply = AsyncMock(return_value=[
            {
                "supply_order_id": "SO-1",
                "supplier_id": "SUP-1",
                "quantity_ordered": 100,
                "quantity_received": 0,
                "expected_date": "2026-06-30T00:00:00+00:00",
            },
        ])
        with patch("app.core.atp.get_current_inventory", mock_inv), \
             patch("app.core.atp.get_open_supply", mock_supply):
            result = await rule_based_atp(
                session=AsyncMock(),
                tenant_id=UUID(int=1),
                product_id=UUID(int=10),
                quantity=80,
                required_date=datetime(2026, 6, 28, tzinfo=UTC),
                delay_buffer_days=3.0,
            )
        assert result["is_available"] is False
        assert result["shortage"] == 70.0
        assert result["supply_contribution_breakdown"][0]["arrives_on_time"] is False

    @pytest.mark.asyncio
    async def test_no_supply_only_on_hand(self):
        mock_inv = AsyncMock(
            return_value={"qty_on_hand": 30, "qty_reserved": 5, "qty_in_transit": 0}
        )
        mock_supply = AsyncMock(return_value=[])
        with patch("app.core.atp.get_current_inventory", mock_inv), \
             patch("app.core.atp.get_open_supply", mock_supply):
            result = await rule_based_atp(
                session=AsyncMock(),
                tenant_id=UUID(int=1),
                product_id=UUID(int=10),
                quantity=25,
                required_date=datetime(2026, 7, 1, tzinfo=UTC),
            )
        assert result["is_available"] is True
        assert result["available_now"] == 25.0
        assert result["shortage"] == 0.0
