import os
from uuid import uuid4

os.environ.setdefault("IPE_JWT_SECRET_KEY", "dev-jwt-secret-change-in-production-min-32-chars")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from ipe_shared.testing.conftest_helpers import apply_unit_test_env_defaults

apply_unit_test_env_defaults()

import pytest

from ipe_shared.config import settings
from ipe_shared.database.connection import close_database, init_database
from ipe_shared.testing.conftest_helpers import (
    apply_unit_test_env_defaults,
    patch_unit_test_health_probes,
    apply_auth_and_session_overrides,
    apply_session_override,
    clear_overrides,
    make_auth_headers as _make_auth_headers,
)


@pytest.fixture(scope="session")
def event_loop():
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def _mock_health_probes(monkeypatch):
    patch_unit_test_health_probes(monkeypatch)


@pytest.fixture(autouse=True)
async def db():
    try:
        await init_database(settings.DATABASE_URL)
    except Exception:
        pass
    yield
    try:
        await close_database()
    except Exception:
        pass


@pytest.fixture
def app():
    from app.main import create_app

    _app = create_app()
    apply_auth_and_session_overrides(_app)
    yield _app
    clear_overrides(_app)


@pytest.fixture
def rbac_app():
    from app.main import create_app

    _app = create_app()
    apply_session_override(_app)
    yield _app
    clear_overrides(_app)


@pytest.fixture
async def client(app):
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def rbac_client(rbac_app):
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=rbac_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    return _make_auth_headers(role="planner")


@pytest.fixture
def admin_auth_headers():
    return _make_auth_headers(role="admin")
