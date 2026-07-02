from app.core.forecaster import forecast_series, mape, simple_exponential_smoothing


def test_exponential_smoothing():
    history = [10.0, 12.0, 11.0, 13.0, 12.0]
    value = simple_exponential_smoothing(history)
    assert 10.0 < value < 13.0


def test_forecast_series_length():
    points = forecast_series([10.0, 12.0, 11.0], 5)
    assert len(points) == 5
    assert all("value" in p for p in points)


def test_mape():
    assert mape([100.0, 200.0], [110.0, 180.0]) == 10.0
