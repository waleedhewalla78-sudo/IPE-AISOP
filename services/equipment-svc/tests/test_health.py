from app.core.health import predict_failure_date, rul_to_health_score


def test_rul_health_score():
    assert rul_to_health_score(200) > rul_to_health_score(24)


def test_critical_prediction():
    pred = predict_failure_date(24)
    assert pred["critical"] is True
