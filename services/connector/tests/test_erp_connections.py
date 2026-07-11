"""Tests for ERP connections API (W1-03/04 Sprint 4)."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient

from app.core.password_crypto import decrypt_password, encrypt_password, reset_key_cache
from ipe_shared.testing.conftest_helpers import (
    V8_TENANT_ID,
    apply_auth_and_session_overrides,
    make_auth_headers,
    reset_v8_test_session,
)

FERNET_KEY = Fernet.generate_key().decode()


@pytest.fixture(autouse=True)
def _encryption_key(monkeypatch):
    monkeypatch.setenv("IPE_ENCRYPTION_KEY", FERNET_KEY)
    reset_key_cache()
    yield
    reset_key_cache()


def test_encrypt_decrypt_roundtrip():
    cipher = encrypt_password("secret-pass")
    assert cipher != "secret-pass"
    assert decrypt_password(cipher) == "secret-pass"


def test_encrypt_missing_key_raises(monkeypatch):
    monkeypatch.delenv("IPE_ENCRYPTION_KEY", raising=False)
    reset_key_cache()
    with pytest.raises(ValueError, match="IPE_ENCRYPTION_KEY"):
        encrypt_password("x")


def _make_row(**overrides):
    base = {
        "id": uuid4(),
        "tenant_id": UUID(V8_TENANT_ID),
        "erp_type": "odoo",
        "display_name": "Star Trans Odoo",
        "host_url": "http://odoo.example.com:8069",
        "database_name": "startrans",
        "username": "admin",
        "password_encrypted": encrypt_password("secret"),
        "api_protocol": "xmlrpc",
        "is_active": True,
        "is_production": False,
        "last_test_at": None,
        "last_test_result": None,
        "last_test_message": None,
        "sync_interval_seconds": 900,
        "sync_enabled": True,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "created_by": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.fixture
async def client(app):
    reset_v8_test_session()
    apply_auth_and_session_overrides(app, tenant_id=UUID(V8_TENANT_ID))
    transport = ASGITransport(app=app)
    headers = make_auth_headers(tenant_id=UUID(V8_TENANT_ID), role="admin")
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_connection_password_not_in_get(client):
    created = _make_row()

    async def fake_create(session, tenant_id, req, created_by=None):
        from app.schemas.erp_connections import ErpConnectionResponse

        return ErpConnectionResponse(
            id=created.id,
            display_name=req.display_name,
            host_url=req.host_url,
            database_name=req.database_name,
            username=req.username,
            erp_type=req.erp_type,
            is_active=True,
            is_production=req.is_production,
            sync_interval_seconds=req.sync_interval_seconds,
            sync_enabled=req.sync_enabled,
        )

    with patch("app.api.v1.erp_connections.svc.create_connection", side_effect=fake_create), patch(
        "app.api.v1.erp_connections.svc.list_connections",
        AsyncMock(
            return_value=[
                __import__("app.schemas.erp_connections", fromlist=["ErpConnectionResponse"]).ErpConnectionResponse(
                    id=created.id,
                    display_name=created.display_name,
                    host_url=created.host_url,
                    database_name=created.database_name,
                    username=created.username,
                    erp_type=created.erp_type,
                    is_active=True,
                    is_production=False,
                    sync_interval_seconds=900,
                    sync_enabled=True,
                )
            ]
        ),
    ):
        res = await client.post(
            "/api/v1/erp/connections",
            json={
                "display_name": "Star Trans Odoo",
                "host_url": "http://odoo.example.com:8069",
                "database_name": "startrans",
                "username": "admin",
                "password": "secret",
                "is_production": False,
                "sync_interval_seconds": 900,
            },
        )
        assert res.status_code == 201
        body = res.json()["data"]
        assert "password" not in body
        assert "password_encrypted" not in body

        listed = await client.get("/api/v1/erp/connections")
        assert listed.status_code == 200
        payload = listed.json()["data"]
        assert isinstance(payload, list)
        for item in payload:
            assert "password" not in item
            assert "password_encrypted" not in item


@pytest.mark.asyncio
async def test_connection_test_success(client):
    row = _make_row()
    with patch(
        "app.api.v1.erp_connections.svc.test_connection",
        AsyncMock(
            return_value={
                "result": "success",
                "message": "Connection successful",
                "response_time_ms": 42.0,
                "odoo_version": "19.0",
                "databases_available": ["startrans"],
            }
        ),
    ):
        res = await client.post(f"/api/v1/erp/connections/{row.id}/test")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["result"] == "success"
    assert data["odoo_version"] == "19.0"


@pytest.mark.asyncio
async def test_connection_test_unreachable(client):
    row = _make_row()
    with patch(
        "app.api.v1.erp_connections.svc.test_connection",
        AsyncMock(
            return_value={
                "result": "unreachable",
                "message": "Host unreachable",
                "response_time_ms": 5.0,
                "odoo_version": None,
                "databases_available": None,
            }
        ),
    ):
        res = await client.post(f"/api/v1/erp/connections/{row.id}/test")
    assert res.json()["data"]["result"] == "unreachable"


@pytest.mark.asyncio
async def test_connection_test_auth_failed(client):
    row = _make_row()
    with patch(
        "app.api.v1.erp_connections.svc.test_connection",
        AsyncMock(
            return_value={
                "result": "auth_failed",
                "message": "Authentication failed",
                "response_time_ms": 12.0,
                "odoo_version": "19.0",
                "databases_available": ["startrans"],
            }
        ),
    ):
        res = await client.post(f"/api/v1/erp/connections/{row.id}/test")
    assert res.json()["data"]["result"] == "auth_failed"


@pytest.mark.asyncio
async def test_activate_swaps_active(client):
    from app.schemas.erp_connections import ErpConnectionResponse

    row = _make_row(is_active=True)
    with patch(
        "app.api.v1.erp_connections.svc.activate_connection",
        AsyncMock(
            return_value=ErpConnectionResponse(
                id=row.id,
                display_name=row.display_name,
                host_url=row.host_url,
                database_name=row.database_name,
                username=row.username,
                erp_type="odoo",
                is_active=True,
                is_production=False,
                sync_interval_seconds=900,
                sync_enabled=True,
            )
        ),
    ) as activate:
        res = await client.post(f"/api/v1/erp/connections/{row.id}/activate")
    assert res.status_code == 200
    assert res.json()["data"]["is_active"] is True
    activate.assert_awaited_once()


@pytest.mark.asyncio
async def test_soft_delete(client):
    row = _make_row()
    with patch(
        "app.api.v1.erp_connections.svc.soft_delete_connection", AsyncMock()
    ) as soft_delete:
        res = await client.delete(f"/api/v1/erp/connections/{row.id}")
    assert res.status_code == 204
    soft_delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_probe_classifies_results():
    from app.core.erp_connections_service import _probe_odoo

    class FakeCommon:
        def version(self):
            return {"server_version": "19.0"}

        def authenticate(self, db, user, password, ctx):
            return False if password == "bad" else 2

    class FakeDb:
        def list(self):
            return ["startrans"]

    def fake_proxy(url, allow_none=True):
        if url.endswith("/common"):
            return FakeCommon()
        return FakeDb()

    with patch("app.core.erp_connections_service.xmlrpc.client.ServerProxy", side_effect=fake_proxy):
        ok = _probe_odoo("http://odoo", "startrans", "admin", "good")
        bad = _probe_odoo("http://odoo", "startrans", "admin", "bad")
    assert ok["result"] == "success"
    assert bad["result"] == "auth_failed"
