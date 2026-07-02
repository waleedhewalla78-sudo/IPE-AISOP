from app.core.design_intel import check_design_compliance, recommend_materials


def test_recommend_materials():
    mats = [
        {"id": "1", "name": "A", "properties_jsonb": {"tensile_mpa": 300}, "cost_per_kg": 3, "sustainability_score": 70},
        {"id": "2", "name": "B", "properties_jsonb": {"tensile_mpa": 500}, "cost_per_kg": 5, "sustainability_score": 60},
    ]
    ranked = recommend_materials(mats, required_tensile_mpa=250, max_cost_per_kg=4)
    assert len(ranked) >= 1
    assert ranked[0]["score"] >= ranked[-1]["score"]


def test_compliance_check():
    rules = [{"process_type": "machining", "parameter_key": "max_hardness_hrc", "max_value": 45, "unit": "HRC"}]
    results = check_design_compliance(rules, "machining", {"max_hardness_hrc": 40})
    assert results[0]["result"] == "pass"
