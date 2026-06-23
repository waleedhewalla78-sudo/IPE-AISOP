from app.core.predictor import predict_defect


class TestDefectPrediction:
    def test_basic_prediction(self):
        result = predict_defect("mo-001")
        assert result.mo_id == "mo-001"
        assert 0 <= result.defect_probability <= 1.0
        assert result.risk_level in ("low", "medium", "high")

    def test_night_shift_increases_risk(self):
        day = predict_defect("mo-day", shift="day")
        night = predict_defect("mo-night", shift="night")
        assert night.defect_probability >= day.defect_probability

    def test_high_defect_operator(self):
        normal = predict_defect("mo-01", operator_id="op-normal")
        high_defect = predict_defect("mo-02", operator_id="op-003")
        assert high_defect.defect_probability >= normal.defect_probability

    def test_overdue_maintenance(self):
        recent = predict_defect("mo-01", days_since_maintenance=5)
        overdue = predict_defect("mo-02", days_since_maintenance=60)
        assert overdue.defect_probability >= recent.defect_probability

    def test_all_risk_factors(self):
        result = predict_defect(
            "mo-high-risk",
            work_center_id="wc-weld-01",
            shift="night",
            operator_id="op-003",
            days_since_maintenance=45,
        )
        assert result.risk_level in ("medium", "high")
        assert len(result.recommended_actions) > 0

    def test_low_risk_no_factors(self):
        result = predict_defect("mo-low-risk", shift="day")
        assert result.defect_probability <= 0.5
        assert result.risk_level == "low"

    def test_recommendations_for_high_risk(self):
        result = predict_defect(
            "mo-critical",
            shift="night",
            days_since_maintenance=60,
        )
        if result.defect_probability > 0.5:
            assert len(result.recommended_actions) > 0