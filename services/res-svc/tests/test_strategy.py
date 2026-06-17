
from app.core.business_score import score_scenario
from app.core.strategy import generate_strategies


class TestGenerateStrategies:
    def test_material_shortage_returns_strategies(self):
        result = generate_strategies("MO-001", "material_shortage")
        assert len(result) > 0
        for s in result:
            assert s["mo_id"] == "MO-001"
            assert "strategy" in s
            assert "cost_impact" in s
            assert "delivery_impact_days" in s

    def test_capacity_overload_returns_strategies(self):
        result = generate_strategies("MO-002", "capacity_overload")
        assert len(result) == 4
        assert any(s["strategy"] == "overtime" for s in result)

    def test_labor_absence_returns_strategies(self):
        result = generate_strategies("MO-003", "labor_absence")
        assert len(result) == 3

    def test_supplier_delay_returns_strategies(self):
        result = generate_strategies("MO-004", "supplier_delay")
        assert len(result) == 3

    def test_quality_issue_returns_strategies(self):
        result = generate_strategies("MO-005", "quality_issue")
        assert len(result) == 3

    def test_maintenance_returns_strategies(self):
        result = generate_strategies("MO-006", "maintenance")
        assert len(result) == 3

    def test_unknown_constraint_falls_back_to_default(self):
        result = generate_strategies("MO-007", "unknown_type")
        assert len(result) == 3
        assert any(s["strategy"] == "reschedule" for s in result)

    def test_cost_impact_scales_with_quantity(self):
        small = generate_strategies("MO-001", "capacity_overload", {"quantity": 1})
        large = generate_strategies("MO-002", "capacity_overload", {"quantity": 10})
        assert large[0]["cost_impact"] > small[0]["cost_impact"]


class TestScoreScenario:
    def test_negative_delivery_impact_scores_max(self):
        result = score_scenario({
            "delivery_impact_days": -3, "cost_impact": 100, "risk": "low",
        })
        assert result["components"]["delivery"] == 1.0
        assert result["business_score"] > 0.5

    def test_high_risk_reduces_score(self):
        low_risk = score_scenario({
            "delivery_impact_days": 0, "cost_impact": 0, "risk": "low",
        })
        high_risk = score_scenario({
            "delivery_impact_days": 0, "cost_impact": 0, "risk": "high",
        })
        assert low_risk["business_score"] > high_risk["business_score"]

    def test_high_cost_reduces_score(self):
        cheap = score_scenario({
            "delivery_impact_days": 0, "cost_impact": 100, "risk": "low",
        })
        expensive = score_scenario({
            "delivery_impact_days": 0, "cost_impact": 50000, "risk": "low",
        })
        assert cheap["business_score"] > expensive["business_score"]

    def test_is_recommended_threshold(self):
        good = score_scenario({
            "delivery_impact_days": 0, "cost_impact": 100, "risk": "low",
        })
        bad = score_scenario({
            "delivery_impact_days": 10, "cost_impact": 50000, "risk": "high",
        })
        assert good["is_recommended"] is True
        assert bad["is_recommended"] is False

    def test_score_between_zero_and_one(self):
        result = score_scenario({
            "delivery_impact_days": 3, "cost_impact": 2000, "risk": "medium",
        })
        assert 0 <= result["business_score"] <= 1.0

    def test_components_contains_all_five_keys(self):
        result = score_scenario({
            "delivery_impact_days": 1, "cost_impact": 500, "risk": "medium",
        })
        assert set(result["components"].keys()) == {
            "delivery", "cost", "risk", "penalty_avoidance", "customer_tier",
        }
