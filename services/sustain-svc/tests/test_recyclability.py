from app.core.recyclability import calculate_recyclability_score, HAZARDOUS_MATERIALS, MATERIAL_RECYCLABILITY


class TestRecyclabilityScore:
    def test_basic_recyclability(self):
        result = calculate_recyclability_score("PROD-001", [
            {"material": "steel", "weight_kg": 5.0, "hazardous": False, "disassembly_steps": 2},
            {"material": "plastic_pvc", "weight_kg": 1.5, "hazardous": False, "disassembly_steps": 3},
        ])
        assert "score" in result
        assert "grade" in result
        assert result["score"] > 0
        assert result["grade"] in ("A", "B", "C", "D", "F")

    def test_hazardous_penalty(self):
        result = calculate_recyclability_score("PROD-001", [
            {"material": "electronics_pcb", "weight_kg": 5.0, "hazardous": True, "disassembly_steps": 6},
        ])
        assert result["hazardous_material_penalty"] > 0

    def test_high_recyclability_grade(self):
        result = calculate_recyclability_score("PROD-001", [
            {"material": "steel", "weight_kg": 10.0, "hazardous": False, "disassembly_steps": 1},
            {"material": "aluminum", "weight_kg": 5.0, "hazardous": False, "disassembly_steps": 2},
        ])
        assert result["score"] >= 70
        assert result["grade"] in ("A", "B")

    def test_low_recyclability_grade(self):
        result = calculate_recyclability_score("PROD-001", [
            {"material": "carbon_fiber", "weight_kg": 10.0, "hazardous": False, "disassembly_steps": 8},
        ])
        assert result["score"] < 50

    def test_recommendations_for_low_disassembly(self):
        result = calculate_recyclability_score("PROD-001", [
            {"material": "steel", "weight_kg": 5.0, "hazardous": False, "disassembly_steps": 8},
        ])
        assert len(result["recommendations"]) > 0

    def test_default_components(self):
        result = calculate_recyclability_score("PROD-001", [])
        assert result["score"] > 0
        assert len(result["breakdown"]) > 0

    def test_breakdown_per_component(self):
        result = calculate_recyclability_score("PROD-001", [
            {"material": "steel", "weight_kg": 3.0, "hazardous": False, "disassembly_steps": 2},
        ])
        assert len(result["breakdown"]) == 1
        assert result["breakdown"][0]["material"] == "steel"
        assert result["breakdown"][0]["recyclability_pct"] > 0