from datetime import UTC, datetime, timedelta

from app.core.priority import compute_priority_score


class TestMarginFallbackAbsolute:
    def test_margin_fallback_absolute(self):
        result = compute_priority_score({
            "required_date": (datetime.now(UTC) + timedelta(days=10)).isoformat(),
            "margin_pct": 30.0,
            "customer_tier": 2,
        })
        assert "priority_score" in result
        assert 0 <= result["priority_score"] <= 100
        bd = result["priority_breakdown"]
        assert "margin" in bd
        assert bd["margin"] > 0
