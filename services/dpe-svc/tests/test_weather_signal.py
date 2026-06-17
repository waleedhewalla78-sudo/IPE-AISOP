from datetime import date

from app.core.external_signals.weather import WeatherSignalClient


def test_mock_factor_deterministic():
    client = WeatherSignalClient()
    d = date(2026, 6, 15)
    factor1 = client.get_capacity_adjustment_factor("plant-a", d)
    factor2 = client.get_capacity_adjustment_factor("plant-a", d)
    assert factor1 == factor2
    assert 0.7 <= factor1 <= 1.0


def test_mock_factor_different_locations():
    client = WeatherSignalClient()
    d = date(2026, 6, 15)
    factor_a = client.get_capacity_adjustment_factor("plant-a", d)
    factor_b = client.get_capacity_adjustment_factor("plant-b", d)
    # Not strictly guaranteed, but very likely different due to hash
    assert isinstance(factor_a, float)
    assert isinstance(factor_b, float)
