"""Reusable FastAPI test fixtures for v8 microservices."""

import os

os.environ.setdefault("IPE_JWT_SECRET_KEY", "dev-jwt-secret-change-in-production-min-32-chars")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

import pytest
from httpx import ASGITransport, AsyncClient

from ipe_shared.testing.conftest_helpers import apply_auth_and_session_overrides, clear_overrides

TENANT_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"


@pytest.fixture(scope="session")
def event_loop():
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app_factory():
    def _factory(create_app_fn):
        from uuid import UUID

        app = create_app_fn()
        apply_auth_and_session_overrides(app, role="planner", tenant_id=UUID(TENANT_ID))
        return app

    return _factory


@pytest.fixture
async def client(app_factory, request):
    from app.main import create_app

    app = app_factory(create_app)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    clear_overrides(app)
