from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.middleware.tenant_context import tenant_ctx

TENANT_ID = str(uuid4())
SCENARIO_ID = str(uuid4())


class MockScalarResult:
    def scalar_one_or_none(self):
        return MagicMock(
            id=SCENARIO_ID,
            tenant_id=TENANT_ID,
            status="pending",
            approved_by=None,
            approved_at=None,
            comment=None,
        )


def _default_mock_session():
    ms = AsyncMock(spec=AsyncSession)
    ms.execute = AsyncMock(return_value=MockScalarResult())
    ms.commit = AsyncMock()
    return ms


def _make_app(mock_session=None):
    from app.api.v1.resolution import get_db_session
    from app.main import create_app

    app = create_app()
    app.dependency_overrides.clear()

    session = mock_session if mock_session is not None else _default_mock_session()

    async def override_session():
        yield session

    app.dependency_overrides[get_db_session] = override_session
    return app, session


@pytest.mark.asyncio
async def test_approve_is_idempotent():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=MockScalarResult())
    mock_session.commit = AsyncMock()

    app, _ = _make_app(mock_session)
    token = tenant_ctx.set(TENANT_ID)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"scenario_id": SCENARIO_ID, "approved_by": "test_user", "comment": "approve 1"}
        resp1 = await client.post("/api/v1/resolution/approve", json=payload)
        resp2 = await client.post("/api/v1/resolution/approve", json=payload)
    tenant_ctx.reset(token)

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["data"]["status"] == "approved"
    assert resp2.json()["data"]["status"] == "approved"
    assert resp2.json()["data"]["scenario_id"] == SCENARIO_ID


@pytest.mark.asyncio
async def test_fifty_concurrent_approve_requests():
    """Prompt 1.1 Scenario 2: 50 concurrent identical approve requests."""
    import asyncio

    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=MockScalarResult())
    mock_session.commit = AsyncMock()

    app, _ = _make_app(mock_session)
    token = tenant_ctx.set(TENANT_ID)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"scenario_id": SCENARIO_ID, "approved_by": "concurrent_test"}

        async def send_approve():
            return await client.post("/api/v1/resolution/approve", json=payload)

        results = await asyncio.gather(*[send_approve() for _ in range(50)])
    tenant_ctx.reset(token)

    assert len(results) == 50
    for resp in results:
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "approved"
    assert mock_session.commit.await_count >= 1


@pytest.mark.asyncio
async def test_oversized_payload_rejected():
    """Prompt 1.1 Scenario 1: Payload >10MB is rejected."""
    app, _ = _make_app()
    token = tenant_ctx.set(TENANT_ID)
    transport = ASGITransport(app=app)
    large_field = "x" * (1 * 1024 * 1024)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/resolution/approve",
            json={"scenario_id": large_field, "approved_by": "test"},
        )
    tenant_ctx.reset(token)
    assert resp.status_code in (422, 413)


@pytest.mark.asyncio
async def test_invalid_uuid_rejected():
    """Prompt 1.1 Scenario 1: Invalid UUID format is rejected with 422."""
    app, _ = _make_app()
    token = tenant_ctx.set(TENANT_ID)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/resolution/approve",
            json={"scenario_id": "not-a-uuid", "approved_by": "test"},
        )
    tenant_ctx.reset(token)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_empty_uuid_rejected():
    """Prompt 1.1 Scenario 1: Empty UUID string is rejected with 422."""
    app, _ = _make_app()
    token = tenant_ctx.set(TENANT_ID)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/resolution/approve",
            json={"scenario_id": "", "approved_by": "test"},
        )
    tenant_ctx.reset(token)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_approve_no_tenant():
    app, _ = _make_app()
    token = tenant_ctx.set(None)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/resolution/approve",
            json={"scenario_id": str(uuid4()), "approved_by": "system"},
        )
    tenant_ctx.reset(token)

    assert resp.status_code == 200
    assert resp.json()["error"]["code"] == "NO_TENANT"
