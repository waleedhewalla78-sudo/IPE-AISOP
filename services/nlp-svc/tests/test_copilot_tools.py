"""Tests for copilot tools and agent logic."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.core.copilot_tools import (
    TOOL_DEFINITIONS,
    TOOL_HANDLERS,
    get_order_status,
    get_resource_utilization,
    simulate_disruption,
)


class TestToolDefinitions:
    def test_all_tools_defined(self):
        assert len(TOOL_DEFINITIONS) == 4
        tool_names = {t["name"] for t in TOOL_DEFINITIONS}
        assert "get_order_status" in tool_names
        assert "get_resource_utilization" in tool_names
        assert "simulate_disruption" in tool_names
        assert "get_war_room_recovery" in tool_names

    def test_all_handlers_registered(self):
        assert len(TOOL_HANDLERS) == 4
        for tool in TOOL_DEFINITIONS:
            assert tool["name"] in TOOL_HANDLERS

    def test_tool_schemas_have_required_fields(self):
        for tool in TOOL_DEFINITIONS:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert "properties" in tool["input_schema"]
            assert "required" in tool["input_schema"]


class TestGetOrderStatus:
    @pytest.mark.asyncio
    async def test_success(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {
                "schedule": {
                    "assignments": [
                        {"mo_id": "MO1", "start_minute": 0, "end_minute": 60, "on_time": True, "duration": 60},
                        {"mo_id": "MO1", "start_minute": 70, "end_minute": 130, "on_time": True, "duration": 60},
                    ]
                }
            }
        }
        with patch("app.core.copilot_tools.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_resp)
            result = await get_order_status("MO1", "tenant1")
            assert result["status"] == "scheduled"
            assert result["total_operations"] == 2

    @pytest.mark.asyncio
    async def test_not_found(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": {"schedule": {"assignments": []}}}
        with patch("app.core.copilot_tools.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_resp)
            result = await get_order_status("MO_NONEXISTENT", "tenant1")
            assert result["status"] == "not_scheduled"

    @pytest.mark.asyncio
    async def test_error_handling(self):
        with patch("app.core.copilot_tools.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(side_effect=Exception("Connection refused"))
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await get_order_status("MO1", "tenant1")
            assert result["status"] == "error"


class TestSimulateDisruption:
    @pytest.mark.asyncio
    async def test_full_flow(self):
        clone_resp = MagicMock()
        clone_resp.status_code = 200
        clone_resp.json.return_value = {"data": {"scenario_id": "sc123"}}

        disruption_resp = MagicMock()
        disruption_resp.status_code = 200

        solve_resp = MagicMock()
        solve_resp.status_code = 200

        diff_resp = MagicMock()
        diff_resp.status_code = 200
        diff_resp.json.return_value = {"data": {"impact": {"delayed_orders": 3}, "baseline": {}, "scenario": {}}}

        with patch("app.core.copilot_tools.httpx.AsyncClient") as mock_client:
            instance = mock_client.return_value
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            instance.post = AsyncMock(side_effect=[clone_resp, disruption_resp, solve_resp])
            instance.get = AsyncMock(return_value=diff_resp)
            result = await simulate_disruption("WC1", 8, "tenant1")
            assert result["scenario_id"] == "sc123"
            assert result["downtime_hours"] == 8


class TestGetResourceUtilization:
    @pytest.mark.asyncio
    async def test_success(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {
                "schedule": {
                    "assignments": [
                        {"work_center_id": "WC1", "duration": 120},
                        {"work_center_id": "WC1", "duration": 180},
                        {"work_center_id": "WC2", "duration": 60},
                    ]
                }
            }
        }
        with patch("app.core.copilot_tools.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            result = await get_resource_utilization("WC1", "tenant1")
            assert result["resource_id"] == "WC1"
            assert result["assigned_operations"] == 2
            assert result["total_scheduled_minutes"] == 300
            assert result["utilization_pct"] > 0

    @pytest.mark.asyncio
    async def test_no_assignments(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": {"schedule": {"assignments": []}}}
        with patch("app.core.copilot_tools.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            result = await get_resource_utilization("WC_NONE", "tenant1")
            assert result["assigned_operations"] == 0
            assert result["utilization_pct"] == 0

    @pytest.mark.asyncio
    async def test_error_handling(self):
        with patch("app.core.copilot_tools.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(side_effect=Exception("Connection refused"))
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await get_resource_utilization("WC1", "tenant1")
            assert result["status"] == "error"


class TestGetWarRoomRecovery:
    @pytest.mark.asyncio
    async def test_success(self):
        from app.core.copilot_tools import get_war_room_recovery

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {
                "disruption_id": "d1",
                "impacted_mo_count": 2,
                "recovery_options": [
                    {
                        "rank": 1,
                        "scenario_id": "s1",
                        "business_score_usd": 1000,
                        "activity_cost_usd": 200,
                        "summary": "Expedite",
                    }
                ],
            }
        }
        with patch("app.core.copilot_tools.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_resp)
            result = await get_war_room_recovery("d1", "tenant1")
            assert result["disruption_id"] == "d1"
            assert result["scenario_ids"] == ["s1"]

    @pytest.mark.asyncio
    async def test_non_200(self):
        from app.core.copilot_tools import get_war_room_recovery

        mock_resp = MagicMock()
        mock_resp.status_code = 503
        with patch("app.core.copilot_tools.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_resp)
            result = await get_war_room_recovery(None, "tenant1")
            assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_exception(self):
        from app.core.copilot_tools import get_war_room_recovery

        with patch("app.core.copilot_tools.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(side_effect=Exception("timeout"))
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await get_war_room_recovery("d1", "tenant1")
            assert result["status"] == "error"
