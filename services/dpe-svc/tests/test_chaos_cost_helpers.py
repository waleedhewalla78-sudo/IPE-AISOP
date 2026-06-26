"""Unit tests for chaos_cost pure helpers (no DB)."""

from decimal import Decimal

from app.core.chaos_cost import (
    CHAOS_CATEGORIES,
    _category_for_audit_action,
    _category_for_cause,
    _usd,
)


class TestChaosCostHelpers:
    def test_category_for_cause_idle(self):
        assert _category_for_cause("machine_breakdown") == "idle_time"
        assert _category_for_cause("labor_absence") == "idle_time"

    def test_category_for_cause_rework(self):
        assert _category_for_cause("quality") == "rework"
        assert _category_for_cause("rework_scrap") == "rework"

    def test_category_for_cause_expedite(self):
        assert _category_for_cause("supplier") == "expedite"
        assert _category_for_cause("unknown") == "expedite"

    def test_category_for_cause_fuzzy_match(self):
        assert _category_for_cause("idle_wait") == "idle_time"
        assert _category_for_cause("quality_issue") == "rework"

    def test_category_for_audit_action(self):
        assert _category_for_audit_action("schedule_override") == "idle_time"
        assert _category_for_audit_action("expedite_po") == "expedite"
        assert _category_for_audit_action("unknown_action") == "idle_time"

    def test_usd_none_and_decimal(self):
        assert _usd(None) == 0.0
        assert _usd(Decimal("12.345")) == 12.35
        assert _usd(10) == 10.0

    def test_chaos_categories_structure(self):
        assert set(CHAOS_CATEGORIES.keys()) == {"idle_time", "rework", "expedite"}
        for cfg in CHAOS_CATEGORIES.values():
            assert "label" in cfg
            assert "default_cost_per_minute" in cfg
