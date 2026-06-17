from uuid import UUID

import pytest

TENANT_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "mat-svc"


@pytest.mark.asyncio
async def test_check_availability_no_tenant(client):
    response = await client.post(
        "/api/v1/material/check-availability",
        json={"product_id": str(UUID(int=1)), "quantity": 10, "required_date": "2026-07-01T00:00:00"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == "NO_TENANT"


@pytest.mark.asyncio
async def test_supplier_predict(client):
    response = await client.post("/api/v1/material/supplier-predict", json={})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_netting(client):
    response = await client.post(
        "/api/v1/material/netting",
        json={"product_id": str(UUID(int=1)), "quantity": 100},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_priority_netting_no_tenant(client):
    response = await client.post(
        "/api/v1/material/priority-netting",
        json={
            "product_id": str(UUID(int=1)),
            "demands": [{"id": str(UUID(int=2)), "quantity": 50, "demand_type": "MTO", "priority_score": 0.9}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == "NO_TENANT"


@pytest.mark.asyncio
async def test_rule_based_atp_no_tenant(client):
    response = await client.post(
        "/api/v1/material/check-availability-rule",
        json={
            "product_id": str(UUID(int=1)),
            "quantity": 100,
            "required_date": "2026-07-01T00:00:00",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == "NO_TENANT"
