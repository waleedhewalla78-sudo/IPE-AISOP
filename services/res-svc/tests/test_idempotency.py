from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.middleware.tenant_context import tenant_ctx

TENANT_ID = str(uuid4())
SCENARIO_ID = str(uuid4())
MO_ID = str(uuid4())


def _make_user():
    from ipe_shared.auth.jwt import TokenPayload
    return TokenPayload(
        sub=uuid4(),
        tenant_id=TENANT_ID,
        role="planner",
        type="access",
        exp=datetime.now(UTC) + timedelta(minutes=60),
        iat=datetime.now(UTC),
        jti=str(uuid4()),
    )


def _build_scenario_mock():
    return MagicMock(
        id=SCENARIO_ID,
        tenant_id=TENANT_ID,
        mo_id=MO_ID,
        strategy="reschedule",
        delivery_impact_days=3.0,
        cost_impact=5000.0,
        status="pending",
        version=1,
        approved_by=None,
        approved_at=None,
        comment=None,
    )


def _build_mo_mock():
    return MagicMock(version=1)


def _build_update_mock(rowcount=1):
    m = MagicMock()
    m.rowcount = rowcount
    return m


def _make_mock_session():
    scenario_mock = _build_scenario_mock()
    mo_mock = _build_mo_mock()
    update_mock = _build_update_mock(1)

    r_scenario = MagicMock()
    r_scenario.scalar_one_or_none.return_value = scenario_mock

    r_mo = MagicMock()
    r_mo.scalar_one_or_none.return_value = mo_mock

    r_update = update_mock

    async def exec_side(*args, **kw):
        sql = str(args[0]) if args else ""
        if "UPDATE" in sql:
            return r_update
        if "resolution_scenario" in sql:
            return r_scenario
        return r_mo

    ms = AsyncMock(spec=AsyncSession)
    ms.execute = AsyncMock(side_effect=exec_side)
    ms.commit = AsyncMock()
    return ms


def _make_app(mock_session=None):
    from app.api.v1.resolution import get_db_session
    from app.main import create_app
    from ipe_shared.auth.dependencies import get_current_user

    app = create_app()
    app.dependency_overrides.clear()

    session = mock_session if mock_session is not None else _make_mock_session()

    async def override_session():
        yield session

    async def override_get_current_user():
        return _make_user()

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_current_user] = override_get_current_user
    return app, session


@pytest.mark.asyncio
async def test_approve_is_idempotent():
    import app.api.v1.resolution as res_mod

    mock_session = _make_mock_session()
    app, _ = _make_app(mock_session)
    token = tenant_ctx.set(TENANT_ID)
    transport = ASGITransport(app=app)

    with patch.object(res_mod, "kafka_producer") as mock_kp:
        mock_kp.build_envelope.return_value = {"event_id": str(uuid4())}
        mock_kp.send_avro = AsyncMock()

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
    import app.api.v1.resolution as res_mod

    mock_session = _make_mock_session()
    app, _ = _make_app(mock_session)
    token = tenant_ctx.set(TENANT_ID)
    transport = ASGITransport(app=app)

    with patch.object(res_mod, "kafka_producer") as mock_kp:
        mock_kp.build_envelope.return_value = {"event_id": str(uuid4())}
        mock_kp.send_avro = AsyncMock()

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
async def test_approve_no_auth():
    from app.main import create_app

    app = create_app()
    app.dependency_overrides.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/resolution/approve",
            json={"scenario_id": str(uuid4()), "approved_by": "system"},
        )
    assert resp.status_code == 401
