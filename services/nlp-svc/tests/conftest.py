import os

os.environ.setdefault("IPE_JWT_SECRET_KEY", "dev-jwt-secret-change-in-production-min-32-chars")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
# Unit tests must not prefer live Ollama/OpenRouter from host or docker-compose env.
os.environ["IPE_OLLAMA_ENDPOINT_URL"] = ""
os.environ["IPE_OPENROUTER_API_KEY"] = ""
os.environ.setdefault("IPE_LLM_PRIMARY_PROVIDER", "auto")

import pytest

from ipe_shared.testing.conftest_helpers import (
    apply_auth_and_session_overrides,
    apply_session_override,
    clear_overrides,
    make_auth_headers as _make_auth_headers,
)


@pytest.fixture(autouse=True)
def _isolate_llm_provider_settings(monkeypatch):
    """Keep tier-router unit tests off live Ollama/OpenRouter."""
    from app.config import settings

    monkeypatch.setattr(settings, "OLLAMA_ENDPOINT_URL", "")
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "")
    monkeypatch.setattr(settings, "LLM_PRIMARY_PROVIDER", "auto")


@pytest.fixture
def app():
    from app.main import create_app

    _app = create_app()
    apply_auth_and_session_overrides(_app)
    yield _app
    clear_overrides(_app)


@pytest.fixture
async def client(app):
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def rbac_app():
    from app.main import create_app

    _app = create_app()
    apply_session_override(_app)
    yield _app
    clear_overrides(_app)


@pytest.fixture
async def rbac_client(rbac_app):
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=rbac_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    return _make_auth_headers(role="planner")
