from pytest import approx

from app.core.demand_sensing import disaggregate_weekly_forecast


def test_disaggregate_single_week():
    weekly = [700]
    pattern = [0.20, 0.15, 0.14, 0.13, 0.15, 0.12, 0.11]
    result = disaggregate_weekly_forecast(weekly, pattern)
    assert len(result) == 7
    assert sum(result) == approx(700.0, rel=1e-4)
    assert result[0] == 140.0
    assert result[6] == 77.0


def test_disaggregate_multiple_weeks():
    weekly = [1000, 1200]
    pattern = [0.25, 0.15, 0.15, 0.10, 0.15, 0.10, 0.10]
    result = disaggregate_weekly_forecast(weekly, pattern)
    assert len(result) == 14
    assert sum(result) == approx(2200.0, rel=1e-4)
    assert result[0] == 250.0
    assert result[7] == 300.0


def test_disaggregate_empty_inputs():
    assert disaggregate_weekly_forecast([], [0.2, 0.3, 0.5]) == []
    assert disaggregate_weekly_forecast([100], []) == []


def test_disaggregate_normalizes_pattern():
    weekly = [100]
    pattern = [1, 1, 1, 1, 1, 1, 1]
    result = disaggregate_weekly_forecast(weekly, pattern)
    assert len(result) == 7
    assert sum(result) == 100.0
    assert all(isinstance(v, float) for v in result)
