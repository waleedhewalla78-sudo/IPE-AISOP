"""Tests for Odoo Config v2 API (W1-03–05)."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.schemas.odoo_config_v2 import (
    OdooConfigCreateRequest,
    validate_field_mappings,
)
from ipe_shared.testing.conftest_helpers import (
    V8_TENANT_ID,
    apply_auth_and_session_overrides,
    make_auth_headers,
    make_v8_mock_session,
    reset_v8_test_session,
)


VALID_BODY = {
    "entity_key": "primary",
    "name": "Factory Odoo",
    "odoo_url": "http://odoo.example.com",
    "odoo_db": "ipe_prod",
    "odoo_username": "admin",
    "odoo_password": "secret",
    "enabled": True,
    "sync_interval_minutes": 900,
    "field_mappings": {
        "product": [
            {"ipe_field": "sku", "odoo_model": "product.product", "odoo_field": "default_code"},
        ],
    },
}


@pytest.fixture
def tenant_id():
    return V8_TENANT_ID


@pytest.fixture
async def client(app, tenant_id):
    reset_v8_test_session()
    apply_auth_and_session_overrides(app, tenant_id=__import__("uuid").UUID(tenant_id))
    transport = ASGITransport(app=app)
    headers = make_auth_headers(tenant_id=__import__("uuid").UUID(tenant_id), role="admin")
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        yield ac


def test_field_mappings_json_schema_rejects_invalid():
    with pytest.raises(Exception):
        validate_field_mappings(
            {
                "product": [
                    {"ipe_field": "sku", "odoo_model": "product.product"},
                ]
            }
        )


def test_field_mappings_json_schema_accepts_valid():
    validate_field_mappings(VALID_BODY["field_mappings"])


def test_pydantic_rejects_bad_url():
    body = dict(VALID_BODY)
    body["odoo_url"] = ""
    with pytest.raises(ValidationError):
        OdooConfigCreateRequest.model_validate(body)


def test_pydantic_applies_default_mappings():
    body = dict(VALID_BODY)
    body.pop("field_mappings")
    model = OdooConfigCreateRequest.model_validate(body)
    assert "product" in model.field_mappings
    assert len(model.field_mappings["product"]) >= 1


@pytest.mark.asyncio
async def test_post_invalid_config_returns_422(client):
    bad = dict(VALID_BODY)
    bad["field_mappings"] = {"product": [{"ipe_field": "x"}]}
    res = await client.post("/api/v1/admin/odoo-config", json=bad)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_get_list_empty_without_bootstrap(client):
    res = await client.get("/api/v1/admin/odoo-config")
    assert res.status_code == 200
    payload = res.json()
    assert payload["success"] is True
    assert "entities" in payload["data"]


@pytest.mark.asyncio
async def test_test_connection_success_under_5s(client):
    mock_uid = 7
    mock_version = {"server_version": "19.0"}

    def fake_auth(url, db, user, password):
        return mock_uid, mock_version

    with patch("app.core.odoo_config_service._authenticate_odoo", side_effect=fake_auth):
        res = await client.post(
            "/api/v1/admin/odoo-config/test-connection",
            json={
                "odoo_url": "http://odoo.example.com",
                "odoo_db": "ipe_prod",
                "odoo_username": "admin",
                "odoo_password": "secret",
            },
        )

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["connected"] is True
    assert data["uid"] == mock_uid
    assert data["server_version"] == "19.0"
    assert data["latency_ms"] is not None


@pytest.mark.asyncio
async def test_test_connection_timeout_returns_504(client):
    async def slow_auth(*_args, **_kwargs):
        await asyncio.sleep(10)
        return 1, {}

    with patch("app.core.odoo_config_service.asyncio.to_thread", side_effect=slow_auth):
        with patch("app.core.odoo_config_service.asyncio.wait_for", side_effect=TimeoutError):
            res = await client.post(
                "/api/v1/admin/odoo-config/test-connection",
                json={
                    "odoo_url": "http://odoo.example.com",
                    "odoo_db": "ipe_prod",
                    "odoo_username": "admin",
                    "odoo_password": "secret",
                },
            )

    assert res.status_code == 504
    assert res.json()["detail"]["code"] == "CONNECTION_TIMEOUT"


@pytest.mark.asyncio
async def test_version_conflict_returns_409():
    from app.core.odoo_config_service import create_config_version
    from app.schemas.odoo_config_v2 import OdooConfigCreateRequest

    session = make_v8_mock_session()
    tid = uuid4()

    existing = MagicMock()
    existing.version = 2
    existing.entity_key = "primary"
    existing.name = "Primary"
    existing.odoo_password_enc = None
    existing.odoo_url = "http://x"
    existing.odoo_db = "db"
    existing.odoo_username = "u"
    existing.enabled = True
    existing.sync_interval_minutes = 900
    existing.field_mappings = VALID_BODY["field_mappings"]
    existing.is_current = True

    async def fake_get_current(_session, _tid, _key):
        return existing

    req = OdooConfigCreateRequest.model_validate({**VALID_BODY, "expected_version": 1})

    with patch("app.core.odoo_config_service.get_current_config", fake_get_current):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            await create_config_version(session, tid, req)
        assert exc.value.status_code == 409
        assert exc.value.detail["code"] == "VERSION_CONFLICT"


@pytest.mark.asyncio
async def test_v1_backward_compat_default_mappings():
    body = dict(VALID_BODY)
    body.pop("field_mappings")
    model = OdooConfigCreateRequest.model_validate(body)
    assert model.field_mappings["manufacturing_order"][0].odoo_model == "mrp.production"
