"""Health endpoint alias tests (P7 — /healthz)."""

import pytest
from httpx import ASGITransport, AsyncClient

from ipe_shared.metrics import setup_metrics
from ipe_shared.observability.metrics import setup_health_probes
from fastapi import FastAPI


@pytest.fixture
def health_app():
    app = FastAPI()
    setup_metrics(app, "test-svc", version="9.3.0-p2")
    setup_health_probes(app)
    return app


@pytest.mark.asyncio
async def test_health_endpoint(health_app):
    async with AsyncClient(transport=ASGITransport(app=health_app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_healthz_alias(health_app):
    async with AsyncClient(transport=ASGITransport(app=health_app), base_url="http://test") as client:
        resp = await client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
