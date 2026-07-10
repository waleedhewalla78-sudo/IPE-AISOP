"""Sprint S7 — GET /api/v1/sync/history and data-quality API tests."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from ipe_shared.testing.conftest_helpers import (
    V8_TENANT_ID,
    apply_auth_and_session_overrides,
    make_auth_headers,
    reset_v8_test_session,
)

pytestmark = pytest.mark.asyncio


def _mock_history_rows():
    started = datetime(2026, 7, 10, 8, 0, 0, tzinfo=UTC)
    finished = datetime(2026, 7, 10, 8, 2, 30, tzinfo=UTC)
    return [
        (
            uuid4(),
            "odoo",
            "manual",
            started,
            finished,
            "success",
            {"products": {"updated": 5}},
            None,
        ),
        (
            uuid4(),
            "odoo",
            "scheduled",
            started,
            None,
            "running",
            {},
            None,
        ),
    ]


@pytest.fixture
async def client(app):
    reset_v8_test_session()
    tid = __import__("uuid").UUID(V8_TENANT_ID)
    apply_auth_and_session_overrides(app, tenant_id=tid)
    transport = ASGITransport(app=app)
    headers = make_auth_headers(tenant_id=tid)
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        yield ac


@pytest.mark.asyncio
async def test_sync_history_returns_runs(client, app):
    rows = _mock_history_rows()

    async def fake_execute(stmt, params=None):
        mock = MagicMock()
        mock.fetchall.return_value = rows
        return mock

    session = AsyncMock()
    session.execute = fake_execute

    from ipe_shared.database.session import get_session

    async def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session

    res = await client.get("/api/v1/sync/history", params={"limit": 10})
    assert res.status_code == 200
    payload = res.json()
    assert payload["success"] is True
    assert payload["data"]["count"] == 2
    assert len(payload["data"]["runs"]) == 2
    assert payload["data"]["runs"][0]["status"] == "success"
    assert payload["data"]["runs"][0]["duration_seconds"] == 150.0
    assert payload["data"]["runs"][1]["duration_seconds"] is None


@pytest.mark.asyncio
async def test_sync_history_caps_limit(client, app):
    captured = {}

    async def fake_execute(stmt, params=None):
        captured["limit"] = params.get("lim")
        mock = MagicMock()
        mock.fetchall.return_value = []
        return mock

    session = AsyncMock()
    session.execute = fake_execute

    from ipe_shared.database.session import get_session

    async def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session

    res = await client.get("/api/v1/sync/history", params={"limit": 999})
    assert res.status_code == 200
    assert captured["limit"] == 50


@pytest.mark.asyncio
async def test_sync_data_quality_returns_flags(client, app):
    mo_id = uuid4()

    async def fake_execute(stmt, params=None):
        mock = MagicMock()
        mock.fetchall.return_value = [
            (mo_id, "MO-001", "MISSING_BOM", "No BOM for product", datetime.now(UTC)),
        ]
        return mock

    session = AsyncMock()
    session.execute = fake_execute

    from ipe_shared.database.session import get_session

    async def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session

    res = await client.get("/api/v1/sync/data-quality")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["count"] == 1
    assert data["flags"][0]["flag_code"] == "MISSING_BOM"
    assert data["flags"][0]["erp_mo_id"] == "MO-001"
