import pytest
from app.core.quality_processor import (
    QualityEventInput,
    process_quality_event,
    classify_severity,
    calculate_cost_impact,
    determine_escalation,
    QualityEventType,
    Severity,
    DefectCategory,
)


class TestClassifySeverity:
    def test_critical_by_count(self):
        assert classify_severity(10, None) == "critical"

    def test_major_by_count(self):
        assert classify_severity(5, None) == "major"

    def test_minor_by_count(self):
        assert classify_severity(2, None) == "minor"

    def test_observation_by_count(self):
        assert classify_severity(1, None) == "observation"

    def test_with_category(self):
        assert classify_severity(3, "dimensional") == "minor"


class TestCalculateCostImpact:
    def test_basic(self):
        cost = calculate_cost_impact(1, "dimensional", 0, 0)
        assert cost > 0

    def test_with_scrap(self):
        cost = calculate_cost_impact(1, None, 5, 0)
        assert cost > 500

    def test_with_rework(self):
        cost = calculate_cost_impact(1, None, 0, 3)
        assert cost > 100

    def test_category_multiplier(self):
        dim_cost = calculate_cost_impact(5, "dimensional", 0, 0)
        cos_cost = calculate_cost_impact(5, "cosmetic", 0, 0)
        assert dim_cost > cos_cost


class TestDetermineEscalation:
    def test_executive_on_critical(self):
        assert determine_escalation("critical", 1, 0) == "executive"

    def test_manager_on_major(self):
        assert determine_escalation("major", 1, 0) == "manager"

    def test_supervisor_on_minor(self):
        assert determine_escalation("minor", 1, 0) == "supervisor"

    def test_operator_on_observation(self):
        assert determine_escalation("observation", 1, 0) == "operator"


class TestProcessQualityEvent:
    def test_rework_eligible(self):
        event = QualityEventInput(
            event_type="inspection_fail",
            defect_count=3,
            rework_required=True,
            rework_cycles=0,
            max_rework_cycles=3,
        )
        decision = process_quality_event(event)
        assert decision.action == "rework"
        assert decision.rework_eligible is True
        assert decision.status == "in_rework"

    def test_rework_exhausted_scrap(self):
        event = QualityEventInput(
            event_type="inspection_fail",
            defect_count=10,
            rework_required=True,
            rework_cycles=3,
            max_rework_cycles=3,
        )
        decision = process_quality_event(event)
        assert decision.action == "scrap"
        assert decision.rework_eligible is False

    def test_critical_quarantine(self):
        event = QualityEventInput(
            event_type="defect_detected",
            defect_count=10,
        )
        decision = process_quality_event(event)
        assert decision.requires_quarantine is True
        assert decision.requires_root_cause is True

    def test_minor_no_quarantine(self):
        event = QualityEventInput(
            event_type="inspection_fail",
            defect_count=1,
        )
        decision = process_quality_event(event)
        assert decision.requires_quarantine is False
        assert decision.requires_root_cause is False

    def test_cost_impact_computed(self):
        event = QualityEventInput(
            event_type="inspection_fail",
            defect_count=3,
            scrap_quantity=2,
            rework_cycles=1,
        )
        decision = process_quality_event(event)
        assert decision.impact_summary["cost_impact"] > 0

    def test_escalation_level_set(self):
        event = QualityEventInput(
            event_type="defect_detected",
            defect_count=10,
        )
        decision = process_quality_event(event)
        assert decision.escalation_level == "executive"

    def test_corrective_action_required(self):
        event = QualityEventInput(
            event_type="defect_detected",
            defect_count=1,
            rework_cycles=2,
        )
        decision = process_quality_event(event)
        assert decision.requires_corrective_action is True
