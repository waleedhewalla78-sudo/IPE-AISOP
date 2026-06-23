from app.core.scorer import calculate_circularity_score, MATERIAL_RECOVERY_RATES


class TestCircularityScore:
    def test_basic_score(self):
        result = calculate_circularity_score("PROD-001", [
            {"material": "steel", "weight_kg": 5.0, "recyclable_pct": 92, "join_type": "bolt"},
            {"material": "plastic", "weight_kg": 2.0, "recyclable_pct": 30, "join_type": "snap_fit"},
        ])
        assert "circularity_score" in result
        assert result["material_recovery_pct"] > 0
        assert result["component_count"] == 2
        assert result["total_weight_kg"] == 7.0

    def test_take_back_eligible_when_high_recovery(self):
        result = calculate_circularity_score("PROD-002", [
            {"material": "steel", "weight_kg": 10.0, "recyclable_pct": 95},
        ])
        assert result["take_back_eligible"] is True

    def test_not_eligible_when_low_recovery(self):
        result = calculate_circularity_score("PROD-003", [
            {"material": "plastic", "weight_kg": 10.0, "recyclable_pct": 15},
        ])
        assert result["take_back_eligible"] is False

    def test_disassembly_cost_welded(self):
        result = calculate_circularity_score("PROD-004", [
            {"material": "steel", "weight_kg": 5.0, "recyclable_pct": 90, "join_type": "welded"},
        ])
        assert result["disassembly_cost_total"] > 0

    def test_default_components_when_empty(self):
        result = calculate_circularity_score("PROD-005", [])
        assert result["component_count"] > 0
        assert result["circularity_score"] > 0

    def test_default_material_recovery_rate(self):
        rate = MATERIAL_RECOVERY_RATES.get("default")
        assert rate == 0.40

    def test_steel_has_high_recovery(self):
        assert MATERIAL_RECOVERY_RATES["steel"] > 0.85

    def test_score_uses_override_recyclable_pct(self):
        result = calculate_circularity_score("PROD-006", [
            {"material": "steel", "weight_kg": 1.0, "recyclable_pct": 50, "join_type": "screw"},
        ])
        assert 40 < result["material_recovery_pct"] < 55