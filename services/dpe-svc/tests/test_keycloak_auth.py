"""Keycloak auth endpoint tests."""

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_auth_info_local():
    with patch("ipe_shared.auth.keycloak.auth_provider", return_value="local"):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/auth/info")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["mode"] == "local"


@pytest.mark.asyncio
async def test_auth_info_keycloak():
    with patch(
        "ipe_shared.auth.keycloak.auth_info",
        return_value={
            "mode": "keycloak",
            "keycloak_url": "http://localhost:8180",
            "keycloak_realm": "ipe",
            "keycloak_client_id": "ipe-platform",
        },
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/auth/info")
    assert resp.status_code == 200
    assert resp.json()["data"]["mode"] == "keycloak"
