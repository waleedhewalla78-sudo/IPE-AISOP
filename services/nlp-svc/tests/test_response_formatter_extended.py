"""Extended response_formatter coverage (P8 R1-01)."""

import json

from app.core.response_formatter import format_structured_response, is_llm_error


class TestIsLlmError:
    def test_not_configured(self):
        assert is_llm_error("API key not configured")

    def test_unavailable(self):
        assert is_llm_error("Service unavailable")


class TestFormatStructuredResponse:
    def test_json_string_input(self):
        data = json.dumps({"items": [{"name": "X", "qty_on_hand": 1, "qty_available": 1}]})
        text = format_structured_response("material_status", data)
        assert text and "X" in text

    def test_invalid_json_returns_none(self):
        assert format_structured_response("material_status", "Could not fetch data") is None

    def test_plain_string_non_fetch(self):
        assert format_structured_response("general", "Hello world") == "Hello world"

    def test_non_dict_returns_none(self):
        assert format_structured_response("general", [1, 2]) is None

    def test_error_key(self):
        text = format_structured_response("demand_query", {"error": "timeout"})
        assert "timeout" in text

    def test_demand_query(self):
        data = {"items": [{"product_name": "P1", "quantity": 10, "required_date": "2026-07-01"}]}
        text = format_structured_response("demand_query", data)
        assert "P1" in text

    def test_demand_empty(self):
        assert "No open demand" in format_structured_response("demand_query", {"items": []})

    def test_capacity_bottlenecks(self):
        data = {"bottlenecks": [{"work_center": "WC1", "utilization_pct": 95}]}
        text = format_structured_response("capacity_status", data)
        assert "WC1" in text and "95" in text

    def test_capacity_utilization(self):
        data = {"utilization": [{"work_center": "WC2", "utilization_pct": 80}]}
        text = format_structured_response("capacity_status", data)
        assert "WC2" in text

    def test_capacity_total_ops(self):
        text = format_structured_response("capacity_status", {"total_operations": 12})
        assert "12 operation" in text

    def test_delay_alerts(self):
        data = {"alerts": [{"mo_ref": "MO-1", "cause": "supplier", "delay_minutes": 30}]}
        text = format_structured_response("delay_analysis", data)
        assert "MO-1" in text

    def test_delay_empty(self):
        assert "No active delay" in format_structured_response("delay_analysis", {"alerts": []})

    def test_feasibility_at_risk(self):
        data = {
            "items": [
                {"erp_mo_id": "MO-A", "feasibility_score": 55, "primary_constraint": "material"},
                {"erp_mo_id": "MO-B", "feasibility_score": 90, "primary_constraint": "none"},
            ]
        }
        text = format_structured_response("feasibility_check", data)
        assert "MO-A" in text and "at risk" in text

    def test_resolution_scenarios(self):
        data = {
            "scenarios": [
                {"strategy": "expedite", "mo_id": "MO-1", "status": "proposed", "cost_impact": 5000},
            ]
        }
        text = format_structured_response("resolution_help", data)
        assert "expedite" in text

    def test_resolution_empty(self):
        assert "No resolution scenarios" in format_structured_response("resolution_help", {"scenarios": []})

    def test_general_summary(self):
        assert format_structured_response("general", {"summary": "All clear"}) == "All clear"

    def test_unknown_intent_no_summary(self):
        assert format_structured_response("unknown_intent", {}) is None
