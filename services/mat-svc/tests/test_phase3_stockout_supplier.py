from app.core.predictive_stockout import PredictiveStockout, SupplierReliabilityScorer


def test_stockout_at_risk():
    pred = PredictiveStockout().predict(
        product_code="RM-CW25",
        on_hand=450,
        avg_daily_consumption=65,
        avg_lead_time_days=8,
        lead_time_variability_days=3,
    )
    assert pred["at_risk"] is True
    assert pred["days_of_stock"] < 8
    assert len(pred["recommended_actions"]) >= 1


def test_supplier_score_flags_single_source():
    score = SupplierReliabilityScorer().score(
        supplier_name="Cairo Copper",
        on_time_pct=68,
        quality_rejection_pct=3,
        lead_time_trend="worsening",
        concentration_pct=100,
        sample_size=12,
    )
    assert score["overall_score"] < 70
    assert score["recommendation"]
    assert score["risk_tier"] in ("high", "medium")
