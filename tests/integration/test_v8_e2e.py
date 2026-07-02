"""v8 cross-service integration tests against Kong + live Docker stack.

Requires:
  docker compose -f infrastructure/docker/docker-compose.yml up -d
  alembic upgrade head (029-031)

Usage:
  uv run pytest tests/integration/test_v8_e2e.py -v -m integration
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime

import httpx
import jwt
import pytest

KONG_URL = os.environ.get("TEST_KONG_URL", "http://localhost:8000")
TENANT_ID = os.environ.get("TEST_TENANT_ID", "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
JWT_SECRET = os.environ.get("IPE_JWT_SECRET_KEY", "dev-only-change-in-production-min-32-chars-long!!")
PRODUCT_ID = os.environ.get("TEST_PRODUCT_ID", "abdc613f-643c-4395-a4c7-f6748debe126")
DEMO_USER_ID = os.environ.get("TEST_USER_ID", "c0eebc99-9c0b-4ef8-bb6d-6bb9bd380c03")

pytestmark = [pytest.mark.integration]


def _auth_headers() -> dict[str, str]:
    token = jwt.encode(
        {
            "sub": DEMO_USER_ID,
            "tenant_id": TENANT_ID,
            "role": "planner",
            "exp": datetime.now(UTC).timestamp() + 3600,
            "iat": datetime.now(UTC).timestamp(),
            "jti": str(uuid.uuid4()),
            "type": "access",
        },
        JWT_SECRET,
        algorithm="HS256",
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": TENANT_ID,
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=KONG_URL, timeout=60.0) as c:
        yield c


def test_v8_services_health(client):
    """All v8 microservices reachable via Kong."""
    paths = [
        "/api/v1/demand/forecast",
        "/api/v1/scenario",
        "/api/v1/supply/network",
        "/api/v1/orders",
        "/api/v1/equipment",
        "/api/v1/materials",
        "/api/v1/suppliers",
    ]
    headers = _auth_headers()
    for path in paths:
        r = client.get(path, headers=headers)
        assert r.status_code == 200, f"{path} -> {r.status_code} {r.text[:200]}"
        body = r.json()
        assert body.get("success") is True or "data" in body or "forecasts" in str(body)


def test_v8_demand_to_scenario_flow(client):
    headers = _auth_headers()
    sense = client.post(
        "/api/v1/demand/sense",
        headers=headers,
        json={"horizon": "short", "periods": 7},
    )
    assert sense.status_code == 200
    assert sense.json()["success"] is True

    scenario = client.post(
        "/api/v1/scenario",
        headers=headers,
        json={"name": f"E2E-{uuid.uuid4().hex[:8]}", "description": "v8 integration"},
    )
    assert scenario.status_code == 200
    sid = scenario.json()["data"]["scenario_id"]

    sim = client.post(f"/api/v1/scenario/{sid}/simulate", headers=headers)
    assert sim.status_code == 200
    assert sim.json()["success"] is True


def test_v8_supply_order_flow(client):
    headers = _auth_headers()
    network = client.get("/api/v1/supply/network", headers=headers)
    assert network.status_code == 200
    assert "facilities" in network.json()["data"]

    order = client.post(
        "/api/v1/orders",
        headers=headers,
        json={"lines": [{"product_id": PRODUCT_ID, "quantity": 2, "unit_price": 1}]},
    )
    assert order.status_code == 200
    oid = order.json()["data"]["order_id"]

    listed = client.get("/api/v1/orders", headers=headers)
    assert listed.status_code == 200
    ids = [o["id"] for o in listed.json()["data"]["orders"]]
    assert oid in ids


def test_v8_design_procurement(client):
    headers = _auth_headers()
    mats = client.get("/api/v1/materials", headers=headers)
    assert mats.status_code == 200
    assert mats.json()["data"]["count"] >= 1

    rec = client.post(
        "/api/v1/design/recommend",
        headers=headers,
        json={"required_tensile_mpa": 200, "max_cost_per_kg": 10},
    )
    assert rec.status_code == 200

    spend = client.get("/api/v1/procurement/spend", headers=headers)
    assert spend.status_code == 200
    assert spend.json()["data"]["summary"]["total"] > 0


def test_v8_copilot_role_agents(client):
    headers = _auth_headers()
    agents = client.get("/api/v1/copilot/agents", headers=headers)
    assert agents.status_code == 200
    roles = {a["role"] for a in agents.json()["data"]["agents"]}
    assert "planner" in roles

    session = client.post("/api/v1/copilot/session", headers=headers, json={"role": "planner"})
    assert session.status_code == 200
    assert session.json()["data"]["role"] == "planner"
