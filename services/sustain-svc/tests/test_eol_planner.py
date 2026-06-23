from app.core.eol_planner import calculate_eol_plan, REGULATORY_PHASE_OUT


class TestEolPlan:
    def test_basic_eol_plan(self):
        result = calculate_eol_plan("PROD-001", "EU")
        assert "eol_risk_score" in result
        assert "predicted_eol_date" in result
        assert "phase_out_timeline" in result
        assert result["regulatory_region"] == "EU"

    def test_eu_regulatory_compliance(self):
        result = calculate_eol_plan("PROD-001", "EU")
        assert result["regulatory_compliance"]["rohs"] is True
        assert result["regulatory_compliance"]["weee"] is True

    def test_us_regulatory_compliance(self):
        result = calculate_eol_plan("PROD-001", "US")
        assert result["regulatory_compliance"]["rohs"] is False
        assert result["regulatory_compliance"]["conflict_minerals"] is True

    def test_component_obsolescence(self):
        result = calculate_eol_plan("PROD-001", "EU")
        assert len(result["component_obsolescence"]) > 0
        assert "obsolescence_score" in result["component_obsolescence"][0]

    def test_alternative_sourcing_when_high_risk(self):
        result = calculate_eol_plan("PROD-001", "EU")
        assert isinstance(result["alternative_sourcing"], list)

    def test_phase_out_timeline(self):
        result = calculate_eol_plan("PROD-001", "EU")
        timeline = result["phase_out_timeline"]
        assert "current_phase" in timeline
        assert "predicted_eol_date" in timeline
        assert "phase_out_date" in timeline