import pytest

from app.core.scorer import calculate_feasibility


class TestFeasibilityEdgeCases:
    def test_all_none_defaults(self):
        result = calculate_feasibility()
        assert result["feasibility_score"] == 55.0
        assert result["action_taken"] == "routed_to_resolution"

    def test_null_demand_uses_default(self):
        result = calculate_feasibility(
            demand_score=None,
            bom_score=100.0,
            material_score=100.0,
            capacity_score=100.0,
            labor_score=100.0,
        )
        assert result["feasibility_score"] == 100.0

    def test_null_bom_uses_default(self):
        result = calculate_feasibility(
            demand_score=100.0,
            bom_score=None,
            material_score=100.0,
            capacity_score=100.0,
            labor_score=100.0,
        )
        assert result["feasibility_score"] == 100.0

    def test_all_null_material_capacity_labor_default_to_50(self):
        result = calculate_feasibility(demand_score=100.0, bom_score=100.0)
        expected = 100.0 * 0.05 + 100.0 * 0.05 + 50.0 * 0.35 + 50.0 * 0.30 + 50.0 * 0.25
        assert result["feasibility_score"] == round(expected, 2)

    def test_all_scores_zero(self):
        result = calculate_feasibility(
            demand_score=0.0, bom_score=0.0, material_score=0.0,
            capacity_score=0.0, labor_score=0.0,
        )
        assert result["feasibility_score"] == 0.0
        assert result["risk_level"] == "high"
        assert result["action_taken"] == "routed_to_resolution"

    def test_all_scores_max(self):
        result = calculate_feasibility(
            demand_score=100.0, bom_score=100.0, material_score=100.0,
            capacity_score=100.0, labor_score=100.0,
        )
        assert result["feasibility_score"] == 100.0
        assert result["risk_level"] == "low"
        assert result["action_taken"] == "queued_for_planner"

    def test_scores_clamped_above_100(self):
        result = calculate_feasibility(
            demand_score=150.0, bom_score=200.0, material_score=110.0,
            capacity_score=120.0, labor_score=130.0,
        )
        assert result["feasibility_score"] == 100.0
        for gate in ["demand", "bom", "material", "capacity", "labor"]:
            assert result["gate_scores"][gate] == 100.0

    def test_scores_clamped_below_zero(self):
        result = calculate_feasibility(
            demand_score=-10.0, bom_score=-5.0, material_score=-1.0,
            capacity_score=-20.0, labor_score=-50.0,
        )
        assert result["feasibility_score"] == 0.0
        for gate in ["demand", "bom", "material", "capacity", "labor"]:
            assert result["gate_scores"][gate] == 0.0

    def test_nan_scores_treated_as_none(self):
        result = calculate_feasibility(
            demand_score=float("nan"),
            bom_score=100.0,
            material_score=100.0,
            capacity_score=100.0,
            labor_score=100.0,
        )
        assert result["feasibility_score"] == 100.0

    def test_inf_scores_clamped(self):
        result = calculate_feasibility(
            demand_score=float("inf"),
            bom_score=100.0,
            material_score=100.0,
            capacity_score=100.0,
            labor_score=100.0,
        )
        assert result["feasibility_score"] == 100.0

    @pytest.mark.parametrize("mode", ["autonomous", "suggest", "shadow"])
    def test_edge_score_89_9_suggest_stays_queued(self, mode):
        low = 89.9
        result = calculate_feasibility(
            demand_score=low, bom_score=low, material_score=low,
            capacity_score=low, labor_score=low, autonomy_mode=mode,
        )
        assert result["feasibility_score"] < 90.0
        assert result["action_taken"] == "queued_for_planner"

    @pytest.mark.parametrize("mode", ["autonomous", "suggest", "shadow"])
    def test_edge_score_70_exact_queued(self, mode):
        result = calculate_feasibility(
            demand_score=100.0, bom_score=100.0,
            material_score=100.0, capacity_score=0.0, labor_score=100.0,
            autonomy_mode=mode,
        )
        score = result["feasibility_score"]
        assert score == 70.0
        assert result["action_taken"] == "queued_for_planner"

    def test_material_zero_capacity_labor_100_gives_exact_65(self):
        """Prompt 3.1 Scenario 1: material=0%, capacity=100%, labor=100%.

        Expected: 0.35*0 + 0.30*100 + 0.25*100 + 0.05*100 + 0.05*100 = 65.0
        """
        result = calculate_feasibility(
            demand_score=100.0, bom_score=100.0,
            material_score=0.0, capacity_score=100.0, labor_score=100.0,
        )
        assert result["feasibility_score"] == 65.0
        assert result["primary_constraint"] == "material"
        assert result["action_taken"] == "routed_to_resolution"
        assert result["gate_scores"]["material"] == 0.0

    def test_priority_margin_zero_penalty_null_days_zero(self):
        """Margin=0, Penalty=null, DaysUntilDue=0 — no ZeroDivisionError."""
        result = calculate_feasibility(
            demand_score=0.0, bom_score=0.0, material_score=0.0,
            capacity_score=0.0, labor_score=0.0,
        )
        assert result["feasibility_score"] == 0.0
        assert isinstance(result["feasibility_score"], float)
        assert result["feasibility_score"] == 0.0

    def test_primary_constraint_is_lowest_gate(self):
        result = calculate_feasibility(
            demand_score=100.0, bom_score=90.0,
            material_score=40.0, capacity_score=100.0, labor_score=80.0,
        )
        assert result["primary_constraint"] == "material"

    def test_primary_constraint_tie_goes_to_first_sort(self):
        result = calculate_feasibility(
            demand_score=100.0, bom_score=100.0,
            material_score=50.0, capacity_score=50.0, labor_score=100.0,
        )
        assert result["primary_constraint"] == "material"

    def test_autonomous_score_90_exact_auto_confirms(self):
        result = calculate_feasibility(
            demand_score=100.0, bom_score=100.0,
            material_score=100.0, capacity_score=100.0, labor_score=66.67,
            autonomy_mode="autonomous",
        )
        assert result["feasibility_score"] == 91.67
        assert result["action_taken"] == "auto_confirmed"

    def test_is_feasible_flag_at_threshold(self):
        above = calculate_feasibility(material_score=50.0, capacity_score=50.0, labor_score=50.0)
        assert above["is_feasible"] is True
        below = calculate_feasibility(material_score=0.0, capacity_score=0.0, labor_score=0.0)
        assert below["is_feasible"] is False

    def test_risk_level_transitions(self):
        high = calculate_feasibility(material_score=30.0, capacity_score=30.0, labor_score=30.0)
        assert high["risk_level"] == "high"
        med = calculate_feasibility(material_score=55.0, capacity_score=55.0, labor_score=55.0)
        assert med["risk_level"] == "medium"
        low = calculate_feasibility(material_score=90.0, capacity_score=90.0, labor_score=90.0)
        assert low["risk_level"] == "low"

    def test_output_contains_no_nan_values_for_normal_inputs(self):
        """Assert that NaN never appears in any output field for valid inputs."""
        import math
        result = calculate_feasibility(
            demand_score=80.0, bom_score=90.0, material_score=70.0,
            capacity_score=60.0, labor_score=85.0,
        )
        assert not math.isnan(result["feasibility_score"])
        for gate in ["demand", "bom", "material", "capacity", "labor"]:
            assert not math.isnan(result["gate_scores"][gate])
