from app.core.forecaster_factory import SesForecaster, select_forecaster, forecast_with_factory
from app.core.supply_feedback import adjust_forecast_for_supply, parse_supply_network_event


def test_select_forecaster_ses_for_short_history():
    f, version = select_forecaster([10.0, 11.0, 12.0])
    assert isinstance(f, SesForecaster)
    assert version == "ses-v1"


def test_forecast_with_factory_returns_points():
    points, version = forecast_with_factory([10.0, 12.0, 11.0, 13.0] * 5, 7)
    assert len(points) == 7
    assert version in ("ses-v1", "prophet-v1", "lstm-v1")
    assert "value" in points[0]


def test_supply_network_event_adjustment():
    payload = parse_supply_network_event(
        {"tenant_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", "capacity_utilization_pct": 90, "lead_time_days": 14}
    )
    adjusted, confidence = adjust_forecast_for_supply(100.0, **{k: payload[k] for k in ("capacity_utilization_pct", "lead_time_days")})
    assert adjusted < 100.0
    assert 0.0 < confidence <= 1.0
