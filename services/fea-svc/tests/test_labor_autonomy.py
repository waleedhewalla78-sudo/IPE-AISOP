"""Feasibility labor gate and risk level tests (P8 fea-svc)."""

from app.core.scorer import calculate_feasibility


class TestLaborConstraint:
    def test_labor_primary_when_lowest(self):
        result = calculate_feasibility(
            demand_score=100.0,
            bom_score=100.0,
            material_score=100.0,
            capacity_score=100.0,
            labor_score=25.0,
        )
        assert result["primary_constraint"] == "labor"
        assert result["feasibility_score"] < 91

    def test_medium_risk_band(self):
        result = calculate_feasibility(
            demand_score=85.0,
            bom_score=85.0,
            material_score=75.0,
            capacity_score=80.0,
            labor_score=80.0,
        )
        assert result["risk_level"] in ("medium", "low")
        assert 70 <= result["feasibility_score"] < 91


class TestAutonomyModes:
    def test_suggest_mode_queues(self):
        result = calculate_feasibility(
            demand_score=80.0,
            bom_score=80.0,
            material_score=70.0,
            capacity_score=100.0,
            labor_score=100.0,
            autonomy_mode="suggest",
        )
        assert result["action_taken"] in ("queued_for_planner", "routed_to_resolution")
