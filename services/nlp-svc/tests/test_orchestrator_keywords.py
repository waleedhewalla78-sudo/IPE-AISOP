"""Orchestrator keyword routing tests (P8 nlp-svc — AG-02)."""

import pytest

from app.core.orchestrator import _classify_intent_keywords, _auth_headers


class TestIntentKeywords:
    @pytest.mark.parametrize(
        "query,expected",
        [
            ("Show FG stock levels", "material_status"),
            ("What is demand for Q3?", "demand_query"),
            ("Work center utilization report", "capacity_status"),
            ("Why is MO-123 late?", "delay_analysis"),
            ("Feasibility score for order 456", "feasibility_check"),
            ("Suggest overtime mitigation", "resolution_help"),
            ("Hello there", None),
        ],
    )
    def test_keyword_classification(self, query, expected):
        assert _classify_intent_keywords(query) == expected


class TestAuthHeaders:
    def test_with_bearer(self):
        headers = _auth_headers("tenant-a", "Bearer tok")
        assert headers["X-Tenant-ID"] == "tenant-a"
        assert headers["Authorization"] == "Bearer tok"

    def test_without_bearer(self):
        headers = _auth_headers("tenant-b", None)
        assert headers == {"X-Tenant-ID": "tenant-b"}
