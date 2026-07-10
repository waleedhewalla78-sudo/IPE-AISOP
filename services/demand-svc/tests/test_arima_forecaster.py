from app.core.forecasters.arima_forecaster import ARIMAForecaster, SARIMAForecaster


def test_arima_forecaster_returns_points_with_short_history_fallback():
    points = ARIMAForecaster().predict([10.0, 12.0, 11.0, 13.0], 5)

    assert len(points) == 5
    assert {"value", "lower", "upper"} <= set(points[0])


def test_sarima_forecaster_returns_points_with_short_history_fallback():
    points = SARIMAForecaster().predict([10.0, 12.0, 11.0, 13.0], 3)

    assert len(points) == 3
    assert {"value", "lower", "upper"} <= set(points[0])
