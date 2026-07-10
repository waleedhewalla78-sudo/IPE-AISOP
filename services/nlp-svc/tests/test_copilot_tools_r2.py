"""Sprint S2 — Copilot planning tools (mocked httpx)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.copilot_tools import (
    TOOL_HANDLERS,
    get_feasibility_queue,
    get_material_availability,
    get_mo_status,
    get_otd_metrics,
    get_resolution_scenarios,
    get_schedule,
    get_sync_status,
)

R2_TOOLS = (
    "get_mo_status",
    "get_feasibility_queue",
    "get_schedule",
    "get_otd_metrics",
    "get_material_availability",
    "get_sync_status",
    "get_resolution_scenarios",
)


def _mock_client(*, method: str = "get", status_code: int = 200, json_data: dict | None = None):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data or {"data": {}}

    instance = MagicMock()
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=False)
    if method == "post":
        instance.post = AsyncMock(return_value=mock_resp)
    else:
        instance.get = AsyncMock(return_value=mock_resp)
    return instance


class TestR2ToolRegistry:
    def test_all_r2_handlers_registered(self):
        for name in R2_TOOLS:
            assert name in TOOL_HANDLERS


class TestGetMoStatus:
    @pytest.mark.asyncio
    async def test_success_with_tenant_header(self):
        instance = _mock_client(json_data={"data": {"mos": [{"mo_id": "MO-ST-001", "feasibility_score": 62}]}})
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await get_mo_status("MO-ST-001", "tenant-a")
        assert result["status"] == "ok"
        assert result["mos"][0]["mo_id"] == "MO-ST-001"
        headers = instance.get.await_args.kwargs["headers"]
        assert headers["X-Tenant-ID"] == "tenant-a"


class TestGetFeasibilityQueue:
    @pytest.mark.asyncio
    async def test_success(self):
        instance = _mock_client(json_data={"data": [{"mo_id": "m1", "feasibility_score": 55}]})
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await get_feasibility_queue("tenant-a")
        assert result["status"] == "ok"
        url = instance.get.await_args.args[0]
        assert "/api/v1/feasibility/queue" in url


class TestGetSchedule:
    @pytest.mark.asyncio
    async def test_success(self):
        instance = _mock_client(json_data={"data": {"rows": [{"mo_id": "m1"}]}})
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await get_schedule("tenant-a")
        assert result["status"] == "ok"
        assert result["rows"][0]["mo_id"] == "m1"


class TestGetOtdMetrics:
    @pytest.mark.asyncio
    async def test_primary_success(self):
        instance = _mock_client(json_data={"data": {"otd_pct": 85.2}})
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await get_otd_metrics("tenant-a")
        assert result["status"] == "ok"
        assert result["otd_pct"] == 85.2

    @pytest.mark.asyncio
    async def test_fallback_to_otd_baseline(self):
        fail_resp = MagicMock()
        fail_resp.status_code = 404
        fail_resp.json.return_value = {}

        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"data": {"current_30d": {"otd_pct": 78.0}}}

        instance = MagicMock()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.get = AsyncMock(side_effect=[fail_resp, ok_resp])

        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await get_otd_metrics("tenant-a")
        assert result["status"] == "ok"
        assert result["current_30d"]["otd_pct"] == 78.0


class TestGetMaterialAvailability:
    @pytest.mark.asyncio
    async def test_post_with_body(self):
        instance = _mock_client(
            method="post",
            json_data={"data": {"available": True, "confidence": 0.91}},
        )
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await get_material_availability(
                "prod-uuid",
                100.0,
                "2026-07-15",
                "tenant-a",
            )
        assert result["status"] == "ok"
        assert result["available"] is True
        body = instance.post.await_args.kwargs["json"]
        assert body["product_id"] == "prod-uuid"
        assert body["quantity"] == 100.0


class TestGetSyncStatus:
    @pytest.mark.asyncio
    async def test_success(self):
        instance = _mock_client(json_data={"data": {"last_sync": {"status": "success"}}})
        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await get_sync_status("tenant-a")
        assert result["status"] == "ok"
        assert result["last_sync"]["status"] == "success"
        url = instance.get.await_args.args[0]
        assert "/api/v1/sync/status" in url


class TestGetResolutionScenarios:
    @pytest.mark.asyncio
    async def test_primary_dpe_then_res_fallback(self):
        fail_resp = MagicMock()
        fail_resp.status_code = 404
        fail_resp.json.return_value = {}

        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"data": {"scenarios": [{"id": "s1", "strategy": "expedite"}]}}

        instance = MagicMock()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.get = AsyncMock(side_effect=[fail_resp, ok_resp])

        with patch("app.core.copilot_tools.httpx.AsyncClient", return_value=instance):
            result = await get_resolution_scenarios("mo-uuid", "tenant-a")
        assert result["status"] == "ok"
        assert result["scenarios"][0]["strategy"] == "expedite"
