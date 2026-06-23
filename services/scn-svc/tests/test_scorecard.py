from app.core.scorecard import SCORING_WEIGHTS, calculate_supplier_scorecard, _compute_trend


class TestComputeTrend:
    def test_empty_values(self):
        result = _compute_trend([])
        assert result["direction"] == "stable"
        assert result["change_pct"] == 0.0

    def test_single_value(self):
        result = _compute_trend([85.0])
        assert result["direction"] == "stable"
        assert result["change_pct"] == 0.0

    def test_improving_trend(self):
        result = _compute_trend([70.0, 75.0, 80.0, 85.0])
        assert result["direction"] == "improving"
        assert result["change_pct"] > 0

    def test_declining_trend(self):
        result = _compute_trend([90.0, 85.0, 80.0, 75.0])
        assert result["direction"] == "declining"
        assert result["change_pct"] < 0

    def test_stable_trend(self):
        result = _compute_trend([80.0, 81.0, 80.5, 80.0])
        assert result["direction"] == "stable"

    def test_zero_base(self):
        result = _compute_trend([0.0, 50.0])
        assert result["change_pct"] == 0.0


class TestCalculateSupplierScorecard:
    def test_default_scores(self):
        result = calculate_supplier_scorecard("tenant-1", "supp-1")
        assert result["supplier_id"] == "supp-1"
        assert result["tenant_id"] == "tenant-1"
        assert 0 <= result["composite_score"] <= 100
        assert result["risk_tier"] in ("low", "medium", "high")
        assert len(result["dimension_scores"]) == 5

    def test_custom_scores(self):
        result = calculate_supplier_scorecard(
            "tenant-1",
            "supp-1",
            {
                "otif": {"score": 95.0},
                "quality_defect_rate": {"score": 92.0},
                "cost_competitiveness": {"score": 88.0},
                "sustainability": {"score": 75.0},
                "responsiveness": {"score": 85.0},
            },
        )
        expected = (
            95.0 * 0.35 + 92.0 * 0.25 + 88.0 * 0.20 + 75.0 * 0.10 + 85.0 * 0.10
        )
        assert abs(result["composite_score"] - round(expected, 2)) < 0.01

    def test_high_risk_tier(self):
        result = calculate_supplier_scorecard(
            "tenant-1",
            "supp-1",
            {
                "otif": {"score": 30.0},
                "quality_defect_rate": {"score": 40.0},
                "cost_competitiveness": {"score": 50.0},
                "sustainability": {"score": 20.0},
                "responsiveness": {"score": 30.0},
            },
        )
        assert result["composite_score"] < 60
        assert result["risk_tier"] == "high"

    def test_low_risk_tier(self):
        result = calculate_supplier_scorecard(
            "tenant-1",
            "supp-1",
            {
                "otif": {"score": 95.0},
                "quality_defect_rate": {"score": 98.0},
                "cost_competitiveness": {"score": 90.0},
                "sustainability": {"score": 85.0},
                "responsiveness": {"score": 92.0},
            },
        )
        assert result["composite_score"] >= 80
        assert result["risk_tier"] == "low"

    def test_medium_risk_tier(self):
        result = calculate_supplier_scorecard(
            "tenant-1",
            "supp-1",
            {
                "otif": {"score": 65.0},
                "quality_defect_rate": {"score": 70.0},
                "cost_competitiveness": {"score": 68.0},
                "sustainability": {"score": 60.0},
                "responsiveness": {"score": 65.0},
            },
        )
        assert 60 <= result["composite_score"] < 80
        assert result["risk_tier"] == "medium"

    def test_weights_sum_to_one(self):
        total = sum(SCORING_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_dimension_scores_structure(self):
        result = calculate_supplier_scorecard("tenant-1", "supp-1")
        for dim in ["otif", "quality_defect_rate", "cost_competitiveness", "sustainability", "responsiveness"]:
            assert dim in result["dimension_scores"]
            assert "score" in result["dimension_scores"][dim]
            assert "weight" in result["dimension_scores"][dim]
            assert result["dimension_scores"][dim]["weight"] == SCORING_WEIGHTS[dim]

    def test_historical_trends(self):
        result = calculate_supplier_scorecard(
            "tenant-1",
            "supp-1",
            {
                "otif": {"score": 85.0, "history": [80.0, 82.0, 85.0]},
                "quality_defect_rate": {"score": 90.0, "history": [85.0, 88.0, 90.0]},
            },
        )
        assert "30d" in result["historical_trends"]
        assert "90d" in result["historical_trends"]
        assert "365d" in result["historical_trends"]

    def test_scores_clamped(self):
        result = calculate_supplier_scorecard(
            "tenant-1",
            "supp-1",
            {
                "otif": {"score": 150.0},
                "quality_defect_rate": {"score": -10.0},
            },
        )
        assert result["dimension_scores"]["otif"]["score"] == 100.0
        assert result["dimension_scores"]["quality_defect_rate"]["score"] == 0.0

    def test_computed_at_present(self):
        result = calculate_supplier_scorecard("tenant-1", "supp-1")
        assert "computed_at" in result
        assert result["computed_at"] is not None