import os

os.environ.setdefault("IPE_JWT_SECRET_KEY", "dev-jwt-secret-change-in-production-min-32-chars")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

import pytest
import pytest_asyncio

from ipe_shared.testing.conftest_helpers import (
    apply_auth_and_session_overrides,
    clear_overrides,
)


@pytest.fixture(scope="session")
def app():
    from app.main import create_app

    _app = create_app()
    apply_auth_and_session_overrides(_app)
    yield _app
    clear_overrides(_app)


@pytest_asyncio.fixture(scope="function")
async def client(app):
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
