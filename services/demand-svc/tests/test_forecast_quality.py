import pytest

from app.core.forecast_quality import (
    bias_pct_from_pair,
    mape_from_pair,
    mase_component,
    naive_mae,
    stability_change_pct,
    value_add_pct,
)


def test_mape_and_bias_known_values():
    assert mape_from_pair(100, 80) == 25.0
    assert bias_pct_from_pair(100, 80) == 25.0

    assert mape_from_pair(100, 120) == pytest.approx(16.6667)
    assert bias_pct_from_pair(100, 120) == pytest.approx(-16.6667)


def test_zero_actual_is_skipped():
    assert mape_from_pair(100, 0) is None
    assert bias_pct_from_pair(100, 0) is None
    assert mape_from_pair([100, 110], [0, 100]) == 10.0


def test_naive_mae_and_mase_component():
    baseline = naive_mae([100, 110, 90, 105])
    assert baseline == 15.0
    assert mase_component(30, baseline) == 2.0


def test_stability_and_value_add():
    assert stability_change_pct(100, 130) == 30.0
    assert value_add_pct(25, 18) == 28.0
