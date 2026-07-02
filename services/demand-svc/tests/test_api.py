from datetime import UTC, datetime
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["service"] == "demand-svc"


@pytest.mark.asyncio
async def test_get_forecast_empty(client, auth_headers):
    r = await client.get("/api/v1/demand/forecast", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["forecasts"] == []


@pytest.mark.asyncio
async def test_ingest_signals(client, auth_headers):
    payload = {
        "signals": [
            {
                "source_type": "pos",
                "source_id": "store-1",
                "signal_ts": datetime.now(UTC).isoformat(),
                "value": 42.0,
            }
        ]
    }
    r = await client.post("/api/v1/demand/signal/ingest", json=payload, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["data"]["ingested"] == 1


@pytest.mark.asyncio
async def test_forecast_accuracy(client, auth_headers):
    r = await client.get("/api/v1/demand/accuracy", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["success"] is True
