import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("IPE_JWT_SECRET_KEY", "dev-jwt-secret-change-in-production-min-32-chars")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

import pytest
from httpx import ASGITransport, AsyncClient

from ipe_shared.testing.conftest_helpers import apply_v8_api_overrides, clear_overrides, make_auth_headers, V8_TENANT_ID


@pytest.fixture(scope="session")
def event_loop():
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app():
    from app.main import create_app

    _app = create_app()
    apply_v8_api_overrides(_app, role="planner")
    yield _app
    clear_overrides(_app)


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    from uuid import UUID

    return make_auth_headers(role="planner", tenant_id=UUID(V8_TENANT_ID))
