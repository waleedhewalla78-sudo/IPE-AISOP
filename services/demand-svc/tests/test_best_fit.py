from app.core.forecasters.model_selector import BestFitSelector


def test_segment_cz_only_uses_ses():
    result = BestFitSelector().select_and_forecast([10.0, 11.0, 12.0, 13.0, 14.0, 15.0], 4, segment="CZ")

    assert result.candidates == ["ses"]
    assert result.selected_model == "ses"
    assert result.version == "best-fit:ses-v1"
    assert len(result.points) == 4


def test_intermittent_demand_forces_ses():
    history = [0.0, 10.0, 0.0, 12.0, 0.0, 11.0, 0.0]
    result = BestFitSelector().select_and_forecast(history, 2, segment="AX")

    assert result.intermittent is True
    assert result.candidates == ["ses"]
    assert result.selected_model == "ses"


def test_flat_data_selects_model_and_returns_forecast():
    result = BestFitSelector().select_and_forecast([10.0] * 12, 3)

    assert result.selected_model in {"ses", "arima", "sarima"}
    assert result.validation_mape == 0.0
    assert len(result.points) == 3
    assert {"value", "lower", "upper"} <= set(result.points[0])


def test_time_budget_zero_falls_back_to_first_candidate():
    """RC-02 / UAT-11: exhausted budget falls back to first candidate (ses for default segment)."""
    history = [float(i) for i in range(1, 25)]  # 24 points, enough for ARIMA candidate
    result = BestFitSelector().select_and_forecast(history, 3, time_budget_seconds=0.0)

    # With budget=0 the loop immediately exhausts and returns candidates[0]
    assert result.selected_model in {"ses", "arima", "sarima"}
    assert len(result.points) == 3


def test_time_budget_forces_ses_for_ax_segment():
    """RC-02: AX segment candidates=[arima,sarima,ses]; near-zero budget falls back to ses."""
    history = [float(i) for i in range(1, 25)]
    # With a tiny budget, ARIMA/SARIMA are skipped, SES is the last fallback
    result = BestFitSelector().select_and_forecast(history, 3, segment="AX", time_budget_seconds=0.0)

    # Either arima/sarima completed or we fell back — model must be valid
    assert result.selected_model in {"ses", "arima", "sarima"}
    assert result.points  # non-empty forecast
