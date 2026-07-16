"""Phase 6A — A14 Analytics Intelligence unit tests."""

from app.core.phase6 import (
    build_predictions,
    detect_anomaly,
    detect_trend,
    generate_insights,
    predict_next,
)


def test_trend_detects_rising():
    t = detect_trend([175, 181, 186, 190, 193, 196], label="copper")
    assert t["direction"] == "rising"
    assert t["pct_change"] > 0
    assert t["slope"] > 0


def test_trend_flat_series():
    t = detect_trend([100, 100, 101, 100, 100])
    assert t["direction"] == "flat"


def test_anomaly_flags_drop():
    a = detect_anomaly([120, 122, 119, 121, 118, 90], label="throughput", z_threshold=2.0)
    assert a["anomaly"] is True
    assert a["direction"] == "drop"
    assert a["z_score"] < 0


def test_anomaly_graceful_on_short_series():
    a = detect_anomaly([1, 2], label="x")
    assert a["anomaly"] is False
    assert a["reason"] == "insufficient_data"


def test_anomaly_no_variance():
    a = detect_anomaly([5, 5, 5, 5, 5], label="x")
    assert a["anomaly"] is False
    assert a["reason"] == "no_variance"


def test_predict_next_linear():
    p = predict_next([10, 20, 30, 40], periods=2)
    assert p["method"] == "linear_regression"
    assert len(p["predictions"]) == 2
    # Continuing +10 trend → ~50, ~60.
    assert p["predictions"][0] > 40
    assert 0.3 <= p["confidence"] <= 0.95


def test_predict_carry_forward_short():
    p = predict_next([42], periods=3)
    assert p["method"] == "carry_forward"
    assert p["predictions"] == [42.0, 42.0, 42.0]


def test_generate_insights_default_report():
    r = generate_insights()
    assert r["agent_id"] == "A14"
    assert r["generated"] >= 3
    categories = {i["category"] for i in r["insights"]}
    assert "cost_trend" in categories
    assert "anomaly" in categories or "financial_pattern" in categories
    # Each insight has an action + confidence.
    for i in r["insights"]:
        assert i["suggested_action"]
        assert 0.0 <= i["confidence"] <= 1.0


def test_build_predictions_per_sku():
    r = build_predictions()
    assert set(r["demand_predictions"].keys()) == {"DT100", "DT250", "PT500"}
    assert "gross_margin" in r["financial_predictions"]
    # Honesty: market feed flagged as OPEN.
    assert "PH1-02" in r["financial_predictions"]["note"]
