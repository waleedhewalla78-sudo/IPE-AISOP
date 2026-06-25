"""MDR quality gate fail-closed behavior on /capacity/schedule."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_schedule_mdr_gate_blocks_low_quality(client, auth_headers):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": {
            "overall_score": 65,
            "ai_scheduling_allowed": False,
            "remediation": ["Fix BOM gaps"],
        },
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.api.v1.capacity.httpx.AsyncClient", return_value=mock_client):
        response = await client.post(
            "/api/v1/capacity/schedule",
            json={},
            headers=auth_headers,
        )

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "MDR_QUALITY_GATE_FAILED"
    assert body["error"]["details"]["quality_score"] == 65
    assert body["error"]["details"]["threshold"] == 70


@pytest.mark.asyncio
async def test_schedule_mdr_gate_allows_high_quality(client, auth_headers):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": {
            "overall_score": 85,
            "ai_scheduling_allowed": True,
        },
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.api.v1.capacity.httpx.AsyncClient", return_value=mock_client):
        response = await client.post(
            "/api/v1/capacity/schedule",
            json={},
            headers=auth_headers,
        )

    assert response.status_code == 200
    assert response.json()["error"] is None or response.json().get("success") is not False


@pytest.mark.asyncio
async def test_schedule_mdr_gate_fail_closed_on_exception(client, auth_headers):
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=ConnectionError("dpe-svc unreachable"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.api.v1.capacity.httpx.AsyncClient", return_value=mock_client):
        response = await client.post(
            "/api/v1/capacity/schedule",
            json={},
            headers=auth_headers,
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "MDR_QUALITY_GATE_FAILED"
