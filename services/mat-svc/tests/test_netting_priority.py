"""Unit tests for netting priority constants and sorting logic."""

from app.core.netting import DEMAND_TYPE_PRIORITY


class TestNettingPriority:
    def test_demand_type_priority_order(self):
        assert DEMAND_TYPE_PRIORITY["MTO"] < DEMAND_TYPE_PRIORITY["MTS"]
        assert DEMAND_TYPE_PRIORITY["ETO"] == DEMAND_TYPE_PRIORITY["MTO"]

    def test_demand_sort_key(self):
        demands = [
            {"demand_type": "MTS", "priority_score": 100, "required_date": "2026-07-01"},
            {"demand_type": "MTO", "priority_score": 50, "required_date": "2026-06-01"},
            {"demand_type": "MTO", "priority_score": 90, "required_date": "2026-06-15"},
        ]
        sorted_demands = sorted(
            demands,
            key=lambda d: (
                DEMAND_TYPE_PRIORITY.get(d.get("demand_type", "MTO"), 0),
                -float(d.get("priority_score", 0) or 0),
                d.get("required_date", ""),
            ),
        )
        assert sorted_demands[0]["demand_type"] == "MTO"
        assert sorted_demands[0]["priority_score"] == 90
        assert sorted_demands[-1]["demand_type"] == "MTS"

    def test_unknown_demand_type_defaults_mto(self):
        assert DEMAND_TYPE_PRIORITY.get("UNKNOWN", 0) == 0
