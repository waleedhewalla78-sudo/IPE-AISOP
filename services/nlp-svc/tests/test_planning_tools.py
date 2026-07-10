"""Tests for planning intelligence Copilot tools (mocked HTTP)."""

from __future__ import annotations

import pytest

from app.core import copilot_tools as tools


@pytest.mark.asyncio
async def test_planning_tools_registered():
    expected = {
        "get_forecast_accuracy",
        "get_forecast_bias",
        "get_product_segments",
        "get_safety_stock_gaps",
        "get_capacity_alerts",
        "get_capacity_ranking",
        "get_sop_cycle_status",
        "get_consensus_vs_plan",
        "compare_sop_versions",
    }
    names = {d["name"] for d in tools.TOOL_DEFINITIONS}
    assert expected.issubset(names)
    for name in expected:
        assert name in tools.TOOL_HANDLERS


@pytest.mark.asyncio
async def test_get_forecast_accuracy_ok(monkeypatch):
    async def fake_get(url, tenant_id, *, params=None, timeout=10.0):
        assert "error/mape" in url
        return {"status": "ok", "summary": {"weighted_mape": 18.3}}

    monkeypatch.setattr(tools, "_planning_get", fake_get)
    result = await tools.get_forecast_accuracy("tenant-1", lag=3)
    assert result["status"] == "ok"
    assert result["summary"]["weighted_mape"] == 18.3


@pytest.mark.asyncio
async def test_get_capacity_alerts_error(monkeypatch):
    async def fake_get(url, tenant_id, *, params=None, timeout=10.0):
        return {"status": "error", "message": "HTTP 500 from cap-svc"}

    monkeypatch.setattr(tools, "_planning_get", fake_get)
    result = await tools.get_capacity_alerts("tenant-1")
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_unreachable_service(monkeypatch):
    async def fake_get(url, tenant_id, *, params=None, timeout=10.0):
        return {"status": "error", "message": "Connection refused", "url": url}

    monkeypatch.setattr(tools, "_planning_get", fake_get)
    result = await tools.get_sop_cycle_status("tenant-1")
    assert result["status"] == "error"
    assert "Connection" in result["message"] or "url" in result
