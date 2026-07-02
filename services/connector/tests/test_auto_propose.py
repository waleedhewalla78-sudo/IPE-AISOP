"""Tests for auto-propose resolution scenarios after rescore (FR-R2-01)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.odoo.sync_engine import OdooSyncEngine


@pytest.mark.asyncio
async def test_auto_propose_skips_above_threshold():
    engine = OdooSyncEngine(MagicMock(), "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", AsyncMock())
    client = AsyncMock()
    headers = {"X-Tenant-ID": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"}

    with patch.dict("os.environ", {"AUTO_PROPOSE_THRESHOLD": "75"}):
        count = await engine._auto_propose_scenarios(client, headers, "mo-1", 88.0)

    assert count == 0
    client.post.assert_not_called()


@pytest.mark.asyncio
async def test_auto_propose_calls_res_svc_below_threshold():
    engine = OdooSyncEngine(MagicMock(), "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", AsyncMock())
    client = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "success": True,
        "data": {"scenarios": [{"id": "1"}, {"id": "2"}, {"id": "3"}]},
    }
    client.post = AsyncMock(return_value=mock_resp)
    headers = {"X-Tenant-ID": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"}

    with patch.dict("os.environ", {"AUTO_PROPOSE_THRESHOLD": "75", "RES_SVC_URL": "http://res-svc:8005"}):
        count = await engine._auto_propose_scenarios(client, headers, "mo-1", 52.0)

    assert count == 3
    client.post.assert_called_once()
    call_args = client.post.call_args
    assert "resolution/scenarios" in call_args[0][0]
    assert call_args[1]["json"]["mo_id"] == "mo-1"
