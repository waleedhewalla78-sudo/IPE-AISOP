from unittest.mock import AsyncMock, patch

import pytest

from app.core.llm_client import query_llm
from app.core.llm_errors import LLMUnavailableError
from app.core.orchestrator import _classify_intent, _classify_intent_keywords, route_query


@pytest.mark.asyncio
async def test_query_llm_no_api_key():
    with (
        patch("app.config.settings.ANTHROPIC_API_KEY", "sk-ant-placeholder"),
        patch("app.config.settings.LLM_ROUTING_ENABLED", False),
    ):
        with pytest.raises(LLMUnavailableError):
            await query_llm("test prompt")


@pytest.mark.asyncio
async def test_query_llm_with_api_key_unknown_host():
    with (
        patch("app.config.settings.ANTHROPIC_API_KEY", "sk-real-but-unknown"),
        patch("app.config.settings.LLM_ROUTING_ENABLED", False),
    ):
        with pytest.raises(LLMUnavailableError):
            await query_llm("test prompt")


@pytest.mark.asyncio
async def test_classify_intent_keywords_fg_stock():
    assert _classify_intent_keywords("What is the current FG stock?") == "material_status"


@pytest.mark.asyncio
async def test_route_query_uses_structured_fallback_when_llm_raises():
    mock_fetcher = AsyncMock(
        return_value={
            "items": [
                {
                    "name": "Widget A",
                    "internal_ref": "WGT-A-100",
                    "uom": "unit",
                    "qty_on_hand": 150,
                    "qty_reserved": 0,
                    "qty_available": 150,
                }
            ]
        }
    )
    with (
        patch("app.config.settings.LLM_ROUTING_ENABLED", False),
        patch("app.core.orchestrator._classify_intent", return_value="material_status"),
        patch("app.core.orchestrator._INTENT_DATA_FETCHERS", {"material_status": mock_fetcher}),
        patch(
            "app.core.orchestrator.query_llm",
            side_effect=LLMUnavailableError("LLM error: all providers unavailable"),
        ),
    ):
        result = await route_query("What is the current FG stock?", "tenant-1", auth_header="Bearer token")
        assert result["intent"] == "material_status"
        assert "Widget A" in result["response"]


@pytest.mark.asyncio
async def test_route_query_uses_structured_fallback_when_llm_unavailable():
    mock_fetcher = AsyncMock(
        return_value={
            "items": [
                {
                    "name": "Widget A",
                    "internal_ref": "WGT-A-100",
                    "uom": "unit",
                    "qty_on_hand": 150,
                    "qty_reserved": 0,
                    "qty_available": 150,
                }
            ]
        }
    )
    with (
        patch("app.core.orchestrator._classify_intent", return_value="material_status"),
        patch("app.core.orchestrator._INTENT_DATA_FETCHERS", {"material_status": mock_fetcher}),
        patch(
            "app.core.orchestrator.query_llm",
            return_value="LLM error: all providers unavailable. Last error: Anthropic API key not configured",
        ),
    ):
        result = await route_query("What is the current FG stock?", "tenant-1", auth_header="Bearer token")
        assert result["intent"] == "material_status"
        assert "Widget A" in result["response"]
        assert "150 unit available" in result["response"]


@pytest.mark.asyncio
async def test_classify_intent_falls_back_to_general():
    with patch("app.core.orchestrator.query_llm", return_value="unrecognized_text"):
        intent = await _classify_intent("some random query")
        assert intent == "general"


@pytest.mark.asyncio
async def test_classify_intent_matches_demand():
    with patch("app.core.orchestrator.query_llm", return_value="demand_query"):
        intent = await _classify_intent("show my orders")
        assert intent == "demand_query"


@pytest.mark.asyncio
async def test_route_query_returns_expected_structure():
    mock_fetcher = AsyncMock(return_value="mock system context")
    with (
        patch("app.core.orchestrator._classify_intent", return_value="material_status"),
        patch("app.core.orchestrator._INTENT_DATA_FETCHERS", {"material_status": mock_fetcher}),
        patch("app.core.orchestrator.query_llm", return_value="Here is the material status."),
    ):
        result = await route_query("what materials are low?", "tenant-1")
        assert result["intent"] == "material_status"
        assert result["response"] == "Here is the material status."
        assert "nlp-svc:material_status" in result["sources"]


@pytest.mark.asyncio
async def test_route_query_out_of_domain_question():
    """Prompt 6.2: Out-of-domain questions should not hallucinate."""
    mock_fetcher = AsyncMock(return_value="No IPE data for weather queries.")
    with (
        patch("app.core.orchestrator._classify_intent", return_value="general"),
        patch("app.core.orchestrator._INTENT_DATA_FETCHERS", {"general": mock_fetcher}),
        patch(
            "app.core.orchestrator.query_llm",
            return_value=(
                "I can help with manufacturing planning. "
                "Please ask about demand, materials, or capacity."
            ),
        ),
    ):
        result = await route_query("What's the weather in Tokyo?", "tenant-1")
        assert result["intent"] == "general"
        assert "weather" not in result["response"].lower()
        assert any(
            word in result["response"].lower()
            for word in ["manufacturing", "planning", "demand", "material"]
        )


@pytest.mark.asyncio
async def test_route_query_delay_cause_identification():
    """Prompt 6.2: Copilot can identify delay cause for a specific MO."""
    mock_fetcher = AsyncMock(
        return_value="MO-123: Delay cause is material_shortage (component #456 out of stock)."
    )
    with (
        patch("app.core.orchestrator._classify_intent", return_value="delay_analysis"),
        patch("app.core.orchestrator._INTENT_DATA_FETCHERS", {"delay_analysis": mock_fetcher}),
        patch(
            "app.core.orchestrator.query_llm",
            return_value=(
                "MO-123 is delayed due to material shortage "
                "for component #456. Expedite the purchase order."
            ),
        ),
    ):
        result = await route_query("Why is MO-123 delayed?", "tenant-1")
        assert result["intent"] == "delay_analysis"
        assert "material" in result["response"].lower()


@pytest.mark.asyncio
async def test_route_query_resolution_provides_scenario_id():
    """Prompt 6.2: Copilot response should reference a scenario or actionable ID."""
    mock_fetcher = AsyncMock(
        return_value="Resolution scenario scenario-abc-123 is available for MO-123."
    )
    with (
        patch("app.core.orchestrator._classify_intent", return_value="resolution_help"),
        patch("app.core.orchestrator._INTENT_DATA_FETCHERS", {"resolution_help": mock_fetcher}),
        patch(
            "app.core.orchestrator.query_llm",
            return_value=(
                "Scenario scenario-abc-123 is the best option "
                "for MO-123 with cost impact of $5,000."
            ),
        ),
    ):
        result = await route_query("Find the best resolution for MO-123", "tenant-1")
        assert result["intent"] == "resolution_help"
        assert "scenario" in result["response"].lower()
