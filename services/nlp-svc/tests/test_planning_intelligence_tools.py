"""Tests for Spec-020 planning intelligence Copilot tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.copilot_tools import (
    TOOL_DEFINITIONS,
    TOOL_HANDLERS,
    compare_sop_versions,
    get_capacity_alerts,
    get_capacity_ranking,
    get_consensus_vs_plan,
    get_forecast_accuracy,
    get_forecast_bias,
    get_product_segments,
    get_safety_stock_gaps,
    get_sop_cycle_status,
)

PLANNING_TOOLS = (
    "get_forecast_accuracy",
    "get_forecast_bias",
    "get_product_segments",
    "get_safety_stock_gaps",
    "get_capacity_alerts",
    "get_capacity_ranking",
    "get_sop_cycle_status",
    "get_consensus_vs_plan",
    "compare_sop_versions",
)


def _mock_client(*, status_code: int = 200, json_data: dict | None = None):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data or {"data": {}}

    instance = MagicMock()
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=False)
    instance.get = AsyncMock(return_value=mock_resp)
    return instance


class TestPlanningToolRegistry:
    """All nine planning tools must be in TOOL_HANDLERS and TOOL_DEFINITIONS."""

    def test_all_planning_handlers_registered(self):
        for name in PLANNING_TOOLS:
            assert name in TOOL_HANDLERS, f"{name} missing from TOOL_HANDLERS"

    def test_all_planning_definitions_present(self):
        definition_names = {d["name"] for d in TOOL_DEFINITIONS}
        for name in PLANNING_TOOLS:
            assert name in definition_names, f"{name} missing from TOOL_DEFINITIONS"

    def test_planning_tools_count_at_least_nine(self):
        definition_names = {d["name"] for d in TOOL_DEFINITIONS}
        found = sum(1 for name in PLANNING_TOOLS if name in definition_names)
        assert found >= 9


class TestGetForecastAccuracy:
    @pytest.mark.asyncio
    async def test_success(self):
        instance = _mock_client(json_data={"data": {"mape": 12.5, "bias": -2.1}})
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await get_forecast_accuracy("tenant-a", lag=3)
        assert result["status"] == "ok"
        assert result["mape"] == 12.5

    @pytest.mark.asyncio
    async def test_http_error_returns_error_status(self):
        instance = _mock_client(status_code=503)
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await get_forecast_accuracy("tenant-a")
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_lag_param_passed(self):
        instance = _mock_client(json_data={"data": {"mape": 9.0}})
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            await get_forecast_accuracy("tenant-a", lag=6)
        call_kwargs = instance.get.await_args.kwargs
        assert call_kwargs.get("params", {}).get("lag") == 6


class TestGetForecastBias:
    @pytest.mark.asyncio
    async def test_success(self):
        instance = _mock_client(json_data={"data": {"bias_pct": 5.0, "direction": "over"}})
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await get_forecast_bias("tenant-a", lag=3)
        assert result["status"] == "ok"
        assert result["bias_pct"] == 5.0

    @pytest.mark.asyncio
    async def test_tenant_header_sent(self):
        instance = _mock_client(json_data={"data": {}})
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            await get_forecast_bias("my-tenant")
        headers = instance.get.await_args.kwargs["headers"]
        assert headers["X-Tenant-ID"] == "my-tenant"


class TestGetProductSegments:
    @pytest.mark.asyncio
    async def test_success(self):
        instance = _mock_client(
            json_data={"data": {"segments": [{"segment": "AX", "count": 10, "revenue_share": 45.2}]}}
        )
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await get_product_segments("tenant-a")
        assert result["status"] == "ok"
        assert result["segments"][0]["segment"] == "AX"

    @pytest.mark.asyncio
    async def test_url_contains_segmentation(self):
        instance = _mock_client(json_data={"data": {"segments": []}})
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            await get_product_segments("tenant-a")
        url = instance.get.await_args.args[0]
        assert "segmentation" in url


class TestGetSafetyStockGaps:
    @pytest.mark.asyncio
    async def test_success(self):
        instance = _mock_client(
            json_data={"data": {"understocked_count": 3, "overstocked_count": 1, "gap_value": 12000.0}}
        )
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await get_safety_stock_gaps("tenant-a")
        assert result["status"] == "ok"
        assert result["understocked_count"] == 3

    @pytest.mark.asyncio
    async def test_error_response_on_http_fail(self):
        instance = _mock_client(status_code=500)
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await get_safety_stock_gaps("tenant-a")
        assert result["status"] == "error"


class TestGetCapacityAlerts:
    @pytest.mark.asyncio
    async def test_success(self):
        instance = _mock_client(
            json_data={"data": {"alerts": [{"work_center": "WC-01", "utilisation_pct": 95.0}]}}
        )
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await get_capacity_alerts("tenant-a")
        assert result["status"] == "ok"
        assert result["alerts"][0]["work_center"] == "WC-01"

    @pytest.mark.asyncio
    async def test_url_contains_utilisation(self):
        instance = _mock_client(json_data={"data": {"alerts": []}})
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            await get_capacity_alerts("tenant-a")
        url = instance.get.await_args.args[0]
        assert "utilisation" in url or "utilization" in url or "alert" in url


class TestGetCapacityRanking:
    @pytest.mark.asyncio
    async def test_success_with_top_n(self):
        instance = _mock_client(
            json_data={"data": {"ranking": [{"work_center": "WC-01", "utilisation_pct": 88.0}]}}
        )
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await get_capacity_ranking("tenant-a", top_n=3)
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_top_n_param_passed(self):
        instance = _mock_client(json_data={"data": {"ranking": []}})
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            await get_capacity_ranking("tenant-a", top_n=7)
        call_kwargs = instance.get.await_args.kwargs
        assert call_kwargs.get("params", {}).get("top_n") == 7


class TestGetSopCycleStatus:
    @pytest.mark.asyncio
    async def test_success(self):
        instance = _mock_client(
            json_data={"data": {"cycle_id": "c-001", "cycle_status": "demand_review", "deadline": "2026-07-15"}}
        )
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await get_sop_cycle_status("tenant-a")
        assert result["status"] == "ok"
        assert result["cycle_id"] == "c-001"

    @pytest.mark.asyncio
    async def test_url_contains_sop(self):
        instance = _mock_client(json_data={"data": {}})
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            await get_sop_cycle_status("tenant-a")
        url = instance.get.await_args.args[0]
        assert "sop" in url


class TestGetConsensusVsPlan:
    @pytest.mark.asyncio
    async def test_success(self):
        instance = _mock_client(
            json_data={
                "data": {
                    "consensus_qty": 1000.0,
                    "plan_qty": 950.0,
                    "gap": 50.0,
                    "gap_pct": 5.26,
                }
            }
        )
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await get_consensus_vs_plan("tenant-a")
        assert result["status"] == "ok"
        assert result["consensus_qty"] == 1000.0

    @pytest.mark.asyncio
    async def test_url_contains_reconciliation(self):
        instance = _mock_client(json_data={"data": {}})
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            await get_consensus_vs_plan("tenant-a")
        url = instance.get.await_args.args[0]
        assert "reconciliation" in url or "sop" in url


class TestCompareSopVersions:
    @pytest.mark.asyncio
    async def test_success_with_versions(self):
        instance = _mock_client(
            json_data={"data": {"version_a": "v1", "version_b": "v2", "delta_qty": -50.0}}
        )
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await compare_sop_versions("tenant-a", a="v1", b="v2")
        assert result["status"] == "ok"
        assert result["version_a"] == "v1"

    @pytest.mark.asyncio
    async def test_no_versions_still_calls_endpoint(self):
        instance = _mock_client(json_data={"data": {}})
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await compare_sop_versions("tenant-a")
        assert "status" in result
