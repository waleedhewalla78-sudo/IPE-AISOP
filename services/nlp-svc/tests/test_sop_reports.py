"""Tests for S&OP report API and copilot tools (Sprint S9/S11)."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

TENANT_ID = str(uuid4())


@pytest.mark.asyncio
async def test_analyze_quality_patterns_tool():
    from app.core.copilot_tools import analyze_quality_patterns

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": {"top_bottlenecks": [{"work_center_name": "WC-1", "utilization_pct": 92, "severity": "high"}]}
    }

    with patch("app.core.copilot_tools.httpx.AsyncClient") as mock_client:
        instance = AsyncMock()
        instance.__aenter__.return_value = instance
        instance.__aexit__.return_value = None
        instance.get = AsyncMock(return_value=mock_resp)
        mock_client.return_value = instance

        result = await analyze_quality_patterns(tenant_id=TENANT_ID, lookback_days=30)

    assert result["pattern_count"] >= 1
    assert result["patterns"][0]["pattern"] == "capacity_stress"


@pytest.mark.asyncio
async def test_get_supplier_risk_tool():
    from app.core.copilot_tools import get_supplier_risk

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": {"supplier_count": 2, "high_risk_count": 1}}

    with patch("app.core.copilot_tools.httpx.AsyncClient") as mock_client:
        instance = AsyncMock()
        instance.__aenter__.return_value = instance
        instance.__aexit__.return_value = None
        instance.get = AsyncMock(return_value=mock_resp)
        mock_client.return_value = instance

        result = await get_supplier_risk(tenant_id=TENANT_ID)

    assert result["supplier_count"] == 2


@pytest.mark.asyncio
async def test_sop_report_list_endpoint():
    from httpx import ASGITransport, AsyncClient
    from app.main import create_app
    from ipe_shared.testing.conftest_helpers import apply_auth_and_session_overrides, clear_overrides

    app = create_app()
    apply_auth_and_session_overrides(app)

    with patch(
        "app.api.v1.reports.build_sop_report",
        new=AsyncMock(),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/reports/sop",
                headers={"X-Tenant-ID": TENANT_ID, "Authorization": "Bearer planner-token"},
            )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    clear_overrides(app)
