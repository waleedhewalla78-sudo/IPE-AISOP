import pytest

from app.core.scorer import calculate_feasibility


class TestPrimaryConstraintHonesty:
    def test_material_below_100_returns_material(self):
        result = calculate_feasibility(
            demand_score=100.0, bom_score=100.0, material_score=65.0,
            capacity_score=100.0, labor_score=100.0,
        )
        assert result["primary_constraint"] == "material"

    def test_material_100_returns_none(self):
        result = calculate_feasibility(
            demand_score=100.0, bom_score=100.0, material_score=100.0,
            capacity_score=100.0, labor_score=100.0,
        )
        assert result["primary_constraint"] == "none"

    def test_capacity_can_be_reported_as_constraint(self):
        result = calculate_feasibility(
            demand_score=100.0, bom_score=100.0, material_score=100.0,
            capacity_score=30.0, labor_score=80.0,
        )
        assert result["primary_constraint"] == "capacity"

    def test_demand_or_bom_can_be_constraint(self):
        result = calculate_feasibility(
            demand_score=40.0, bom_score=40.0, material_score=100.0,
            capacity_score=100.0, labor_score=100.0,
        )
        assert result["primary_constraint"] in ("demand", "bom")


class TestActionThresholds:
    def test_91_autonomous_auto_confirms(self):
        result = calculate_feasibility(
            demand_score=100.0, bom_score=100.0, material_score=100.0,
            capacity_score=100.0, labor_score=100.0,
            autonomy_mode="autonomous",
        )
        assert result["action_taken"] == "auto_confirmed"

    def test_75_queued_for_planner(self):
        result = calculate_feasibility(
            demand_score=80.0, bom_score=80.0, material_score=65.0,
            capacity_score=100.0, labor_score=100.0,
            autonomy_mode="shadow",
        )
        assert result["action_taken"] == "queued_for_planner"

    def test_60_routed_to_resolution(self):
        result = calculate_feasibility(
            demand_score=0.0, bom_score=0.0, material_score=0.0,
            capacity_score=100.0, labor_score=100.0,
            autonomy_mode="shadow",
        )
        assert result["feasibility_score"] < 70.0
        assert result["action_taken"] == "routed_to_resolution"
