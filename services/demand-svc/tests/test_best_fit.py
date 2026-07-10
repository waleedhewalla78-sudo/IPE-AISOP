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
