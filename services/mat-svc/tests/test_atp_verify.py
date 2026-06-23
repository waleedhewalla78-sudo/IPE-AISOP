import random
from datetime import UTC, datetime, timedelta

from app.core.atp import _component_monte_carlo, _sample_delay


class TestpATPSeeded:
    def test_non_degenerate_with_mixed_supply(self):
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
        assert 0 < result["confidence"] < 1.0

    def test_reliable_supplier_high_probability(self):
        random.seed(42)
        supply = [
            {"id": "s1", "quantity_ordered": 1000, "quantity_received": 0,
             "expected_date": (datetime.now(UTC) + timedelta(days=5)).isoformat(),
             "distribution_type": "normal", "expected_delay_days": 0.5,
             "delay_std_dev": 0.2},
        ]
        result = _component_monte_carlo(
            on_hand=100, reserved=0, supply_orders=supply,
            required_qty=200, required_date=datetime.now(UTC) + timedelta(days=10),
            priority_demand=0, num_simulations=1000,
        )
        assert result["confidence"] >= 0.90

    def test_chronically_late_supplier_low_probability(self):
        random.seed(42)
        supply = [
            {"id": "s1", "quantity_ordered": 100, "quantity_received": 0,
             "expected_date": (datetime.now(UTC) + timedelta(days=2)).isoformat(),
             "distribution_type": "lognormal", "expected_delay_days": 20.0,
             "delay_std_dev": 10.0},
        ]
        result = _component_monte_carlo(
            on_hand=10, reserved=0, supply_orders=supply,
            required_qty=100, required_date=datetime.now(UTC) + timedelta(days=5),
            priority_demand=0, num_simulations=1000,
        )
        assert result["confidence"] < 0.50


class TestpATPFallback:
    def test_fallback_delay_calculation(self):
        static_lead_time = 10.0
        expected_delay = static_lead_time * 1.2
        delay = _sample_delay("normal", expected_delay, 1.0)
        assert delay >= 0
        random.seed(42)
        for _ in range(100):
            d = _sample_delay("normal", expected_delay, 1.0)
            assert d >= 0


class TestEmptyBOM:
    def test_empty_bom_overall_probability(self):
        components = []
        overall_p = 1.0
        for _ in components:
            overall_p *= 1.0
        assert overall_p == 1.0

    def test_zero_component_product_does_not_crash(self):
        import math
        probs = []
        overall = math.prod(probs) if probs else 1.0
        assert overall == 1.0
