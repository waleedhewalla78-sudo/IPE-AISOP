"""Orchestrator fetchers and routing (P8 R1-01)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.llm_errors import LLMUnavailableError
from app.core.orchestrator import (
    _classify_intent,
    _fetch_capacity_data,
    _fetch_delay_analysis,
    _fetch_demand_data,
    _fetch_feasibility_data,
    _fetch_material_status,
    _fetch_resolution_help,
    route_query,
)


def _mock_client(*, status_code=200, json_data=None, side_effect=None):
    mock_resp = MagicMock()
    mock_resp.is_success = 200 <= status_code < 300
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data or {}

    mock_cli = MagicMock()
    mock_cli.__aenter__ = AsyncMock(return_value=mock_cli)
    mock_cli.__aexit__ = AsyncMock(return_value=False)
    if side_effect:
        mock_cli.get = AsyncMock(side_effect=side_effect)
        mock_cli.post = AsyncMock(side_effect=side_effect)
    else:
        mock_cli.get = AsyncMock(return_value=mock_resp)
        mock_cli.post = AsyncMock(return_value=mock_resp)
    return mock_cli


@pytest.mark.asyncio
async def test_classify_intent_via_llm():
    with patch("app.core.orchestrator.query_llm", return_value="demand_query"):
        assert await _classify_intent("something ambiguous") == "demand_query"


@pytest.mark.asyncio
async def test_classify_intent_llm_fallback_general():
    with patch("app.core.orchestrator.query_llm", return_value="unknown stuff"):
        assert await _classify_intent("xyz") == "general"


@pytest.mark.asyncio
async def test_fetch_demand_success():
    with patch("app.core.orchestrator.httpx.AsyncClient", return_value=_mock_client(json_data={"data": {"demands": [{"id": 1}]}})):
        result = await _fetch_demand_data("t1", auth_header="Bearer x")
        assert result["total"] == 1


@pytest.mark.asyncio
async def test_fetch_demand_http_error():
    with patch("app.core.orchestrator.httpx.AsyncClient", return_value=_mock_client(status_code=503)):
        result = await _fetch_demand_data("t1")
        assert "error" in result


@pytest.mark.asyncio
async def test_fetch_demand_exception():
    with patch("app.core.orchestrator.httpx.AsyncClient", return_value=_mock_client(side_effect=Exception("network"))):
        result = await _fetch_demand_data("t1")
        assert "Could not fetch demand" in result["error"]


@pytest.mark.asyncio
async def test_fetch_material_raw_components():
    with patch("app.core.orchestrator.httpx.AsyncClient", return_value=_mock_client(json_data={"data": {"items": []}})):
        result = await _fetch_material_status("t1", "raw material stock")
        assert "items" in result or result.get("error") is None


@pytest.mark.asyncio
async def test_fetch_material_error():
    with patch("app.core.orchestrator.httpx.AsyncClient", return_value=_mock_client(status_code=500)):
        result = await _fetch_material_status("t1", "stock")
        assert "error" in result


@pytest.mark.asyncio
async def test_fetch_capacity_success():
    payload = {"data": {"bottlenecks": [], "total_operations": 3, "utilization": []}}
    with patch("app.core.orchestrator.httpx.AsyncClient", return_value=_mock_client(json_data=payload)):
        result = await _fetch_capacity_data("t1")
        assert result["total_operations"] == 3


@pytest.mark.asyncio
async def test_fetch_delay_success():
    with patch("app.core.orchestrator.httpx.AsyncClient", return_value=_mock_client(json_data={"data": {"alerts": [{"id": 1}]}})):
        result = await _fetch_delay_analysis("t1")
        assert result["total"] == 1


@pytest.mark.asyncio
async def test_fetch_feasibility_queue():
    with patch("app.core.orchestrator.httpx.AsyncClient", return_value=_mock_client(json_data={"data": [{"mo_id": "1"}]})):
        result = await _fetch_feasibility_data("t1")
        assert result["total"] == 1


@pytest.mark.asyncio
async def test_fetch_feasibility_items_key():
    with patch("app.core.orchestrator.httpx.AsyncClient", return_value=_mock_client(json_data={"items": [{"mo_id": "1"}]})):
        result = await _fetch_feasibility_data("t1")
        assert result["total"] == 1


@pytest.mark.asyncio
async def test_fetch_resolution_success():
    with patch("app.core.orchestrator.httpx.AsyncClient", return_value=_mock_client(json_data={"data": {"scenarios": [{"id": "s1"}] * 12}})):
        result = await _fetch_resolution_help("t1")
        assert result["total"] == 12
        assert len(result["scenarios"]) == 10


@pytest.mark.asyncio
async def test_route_query_llm_unavailable_uses_formatter():
    with (
        patch("app.core.orchestrator._classify_intent", return_value="delay_analysis"),
        patch("app.core.orchestrator._INTENT_DATA_FETCHERS", {"delay_analysis": AsyncMock(return_value={"alerts": []})}),
        patch("app.core.orchestrator.query_llm", side_effect=LLMUnavailableError("down")),
        patch("app.config.settings.LLM_ROUTING_ENABLED", False),
    ):
        result = await route_query("why late?", "tenant-1")
        assert result["intent"] == "delay_analysis"
        assert "No active delay" in result["response"]


@pytest.mark.asyncio
async def test_fetch_material_exception():
    with patch("app.core.orchestrator.httpx.AsyncClient", return_value=_mock_client(side_effect=Exception("timeout"))):
        result = await _fetch_material_status("t1", "stock")
        assert "Could not fetch material" in result["error"]


@pytest.mark.asyncio
async def test_fetch_capacity_exception():
    with patch("app.core.orchestrator.httpx.AsyncClient", return_value=_mock_client(side_effect=Exception("timeout"))):
        result = await _fetch_capacity_data("t1")
        assert "Could not fetch capacity" in result["error"]


@pytest.mark.asyncio
async def test_fetch_feasibility_error_status():
    with patch("app.core.orchestrator.httpx.AsyncClient", return_value=_mock_client(status_code=502)):
        result = await _fetch_feasibility_data("t1")
        assert "error" in result


@pytest.mark.asyncio
async def test_fetch_resolution_exception():
    with patch("app.core.orchestrator.httpx.AsyncClient", return_value=_mock_client(side_effect=Exception("down"))):
        result = await _fetch_resolution_help("t1")
        assert "Could not fetch resolution" in result["error"]


@pytest.mark.asyncio
async def test_fetch_delay_exception():
    with patch("app.core.orchestrator.httpx.AsyncClient", return_value=_mock_client(side_effect=Exception("timeout"))):
        result = await _fetch_delay_analysis("t1")
        assert "Could not fetch delay" in result["error"]


@pytest.mark.asyncio
async def test_route_query_general_intent():
    with (
        patch("app.core.orchestrator._classify_intent", return_value="general"),
        patch("app.core.orchestrator.query_llm", return_value="General help text"),
        patch("app.config.settings.LLM_ROUTING_ENABLED", False),
    ):
        result = await route_query("hello", "tenant-1")
        assert result["intent"] == "general"
        assert result["response"] == "General help text"


@pytest.mark.asyncio
async def test_route_query_llm_error_string_fallback():
    with (
        patch("app.core.orchestrator._classify_intent", return_value="material_status"),
        patch(
            "app.core.orchestrator._INTENT_DATA_FETCHERS",
            {
                "material_status": AsyncMock(
                    return_value={"items": [{"name": "G", "qty_on_hand": 1, "qty_available": 1}]}
                )
            },
        ),
        patch("app.core.orchestrator.query_llm", return_value="LLM error: unavailable"),
        patch("app.config.settings.LLM_ROUTING_ENABLED", False),
    ):
        result = await route_query("stock?", "tenant-1")
        assert "G" in result["response"]
