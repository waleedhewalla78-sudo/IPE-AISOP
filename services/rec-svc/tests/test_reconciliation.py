from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.core.reconciliation import (
    analyze_mo_completion,
    build_retrain_payload,
    calculate_prediction_drift,
    should_trigger_retrain,
)


def _make_mo(
    planned_start=None,
    planned_end=None,
    actual_start=None,
    actual_end=None,
    yield_planned=100,
    yield_actual=None,
    scrap_actual=0,
):
    mo = type("FakeMO", (), {})()
    mo.id = uuid4()
    mo.planned_start = planned_start
    mo.planned_end = planned_end
    mo.actual_start = actual_start
    mo.actual_end = actual_end
    mo.yield_planned = yield_planned
    mo.yield_actual = yield_actual
    mo.scrap_actual = scrap_actual
    return mo


def _make_wo(duration_planned_mins=60, duration_actual_mins=None, status="completed"):
    wo = type("FakeWO", (), {})()
    wo.duration_planned_mins = duration_planned_mins
    wo.duration_actual_mins = duration_actual_mins
    wo.status = status
    return wo


def _make_prediction(predicted_mins, actual_mins, mae_30d=None):
    p = type("FakePred", (), {})()
    p.id = uuid4()
    p.predicted_duration_mins = predicted_mins
    p.actual_duration_mins = actual_mins
    p.mae_30d = mae_30d
    p.created_at = datetime.now(UTC)
    return p


def test_time_variance_calculated_correctly():
    now = datetime.now(UTC)
    mo = _make_mo(
        planned_start=now,
        planned_end=now + timedelta(days=10),
        actual_start=now,
        actual_end=now + timedelta(days=12),
    )
    result = analyze_mo_completion(mo, [])
    assert result["time_variance_pct"] == 20.0
    assert result["planned_duration_days"] == 10.0
    assert result["actual_duration_days"] == 12.0


def test_yield_variance_calculated_correctly():
    now = datetime.now(UTC)
    mo = _make_mo(
        planned_start=now,
        planned_end=now + timedelta(days=5),
        actual_start=now,
        actual_end=now + timedelta(days=5),
        yield_planned=Decimal("100"),
        yield_actual=Decimal("85"),
    )
    result = analyze_mo_completion(mo, [])
    assert result["yield_variance_pct"] == -15.0


def test_scrap_delta_reported():
    now = datetime.now(UTC)
    mo = _make_mo(
        planned_start=now,
        planned_end=now + timedelta(days=3),
        actual_start=now,
        actual_end=now + timedelta(days=3),
        yield_planned=Decimal("50"),
        yield_actual=Decimal("50"),
        scrap_actual=Decimal("5"),
    )
    result = analyze_mo_completion(mo, [])
    assert result["scrap_delta"] == 5.0


def test_time_variance_uses_work_orders_when_no_dates():
    mo = _make_mo(yield_planned=Decimal("100"), yield_actual=Decimal("100"))
    wos = [
        _make_wo(duration_planned_mins=480, duration_actual_mins=600),
        _make_wo(duration_planned_mins=360, duration_actual_mins=420),
    ]
    result = analyze_mo_completion(mo, wos)
    planned_days = (480 + 360) / (24 * 60.0)
    actual_days = (600 + 420) / (24 * 60.0)
    expected_variance = round(((actual_days - planned_days) / planned_days) * 100, 2)
    assert result["time_variance_pct"] == expected_variance


def test_completed_work_order_count():
    now = datetime.now(UTC)
    mo = _make_mo(
        planned_start=now,
        planned_end=now + timedelta(days=5),
        actual_start=now,
        actual_end=now + timedelta(days=5),
    )
    wos = [
        _make_wo(status="completed"),
        _make_wo(status="completed"),
        _make_wo(status="pending"),
    ]
    result = analyze_mo_completion(mo, wos)
    assert result["completed_work_orders"] == 2
    assert result["total_work_orders"] == 3


def test_drift_empty_predictions():
    result = calculate_prediction_drift([])
    assert result["mae"] == 0.0
    assert result["drift_detected"] is False
    assert result["sample_count"] == 0


def test_drift_no_baseline():
    preds = [_make_prediction(100, 110, mae_30d=None)]
    result = calculate_prediction_drift(preds)
    assert result["mae"] == 10.0
    assert result["drift_detected"] is False
    assert result["baseline_mae"] is None


def test_drift_within_threshold():
    preds = [_make_prediction(100, 109, mae_30d=10.0)]
    result = calculate_prediction_drift(preds)
    assert result["mae"] == 9.0
    assert result["drift_detected"] is False
    assert result["drift_pct"] == -10.0


def test_drift_exceeds_threshold():
    preds = [_make_prediction(100, 125, mae_30d=10.0)]
    result = calculate_prediction_drift(preds)
    assert result["mae"] == 25.0
    assert result["drift_detected"] is True
    assert result["drift_pct"] == 150.0


def test_drift_multiple_predictions():
    preds = [
        _make_prediction(100, 110, mae_30d=5.0),
        _make_prediction(200, 220, mae_30d=5.0),
        _make_prediction(150, 165, mae_30d=5.0),
    ]
    result = calculate_prediction_drift(preds)
    assert result["sample_count"] == 3
    assert result["mae"] == 15.0
    assert result["drift_detected"] is True


def test_should_trigger_retrain_drift_detected():
    result = {"drift_detected": True, "sample_count": 50}
    assert should_trigger_retrain(result) is True


def test_should_trigger_retrain_insufficient_samples():
    result = {"drift_detected": True, "sample_count": 20}
    assert should_trigger_retrain(result) is False


def test_should_trigger_retrain_no_drift():
    result = {"drift_detected": False, "sample_count": 50}
    assert should_trigger_retrain(result) is False


def test_build_retrain_payload():
    drift = {"mae": 15.0, "drift_pct": 200.0, "baseline_mae": 5.0}
    records = [{"product_id": "P1", "duration_planned_mins": 60, "duration_actual_mins": 75}]
    payload = build_retrain_payload(drift, records)
    assert payload["trigger_reason"] == "drift_detection"
    assert payload["drift_mae"] == 15.0
    assert payload["drift_pct"] == 200.0
    assert payload["baseline_mae"] == 5.0
    assert len(payload["historical_records"]) == 1
