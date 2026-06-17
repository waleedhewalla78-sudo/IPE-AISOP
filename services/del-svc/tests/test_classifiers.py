import pytest

from app.core.nlp_classifier import classify_by_llm
from app.core.rule_classifier import classify_by_rules


class TestRuleClassifier:
    def test_material_shortage_keyword(self):
        result = classify_by_rules({"source_text": "We ran out of raw material and are short"})
        assert result["cause_category"] == "material_shortage"
        assert 0 < result["confidence"] <= 0.95

    def test_capacity_overload_keyword(self):
        result = classify_by_rules({"source_text": "no capacity, machine is fully booked"})
        assert result["cause_category"] == "capacity_overload"

    def test_labor_absence_keyword(self):
        result = classify_by_rules({"source_text": "operator absent, no show today"})
        assert result["cause_category"] == "labor_absence"

    def test_supplier_delay_keyword(self):
        result = classify_by_rules({"source_text": "shipment delayed, supplier late on delivery"})
        assert result["cause_category"] == "supplier_delay"

    def test_maintenance_keyword(self):
        result = classify_by_rules({"source_text": "machine breakdown, equipment failure"})
        assert result["cause_category"] == "maintenance"

    def test_quality_issue_keyword(self):
        result = classify_by_rules({"source_text": "defect found, quality issue needs rework"})
        assert result["cause_category"] == "quality_issue"

    def test_process_variance_keyword(self):
        result = classify_by_rules({"source_text": "cycle time variance, took longer than expected"})
        assert result["cause_category"] == "process_variance"

    def test_no_match_returns_other(self):
        result = classify_by_rules({"source_text": "everything is going great"})
        assert result["cause_category"] == "other"
        assert result["confidence"] == 0.3

    def test_mo_status_and_work_center_are_included(self):
        result = classify_by_rules({
            "source_text": "",
            "mo_status": "broken machine",
            "work_center_status": "maintenance",
        })
        assert result["cause_category"] == "maintenance"

    def test_matched_keywords_present(self):
        result = classify_by_rules({"source_text": "out of stock shortage"})
        assert len(result["matched_keywords"]) > 0


@pytest.mark.asyncio
async def test_nlp_classifier_no_api_key_returns_other():
    import os
    had_key = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        result = await classify_by_llm("machine breakdown")
        assert result["cause_category"] == "other"
        assert result["confidence"] == 0.0
    finally:
        if had_key is not None:
            os.environ["ANTHROPIC_API_KEY"] = had_key
