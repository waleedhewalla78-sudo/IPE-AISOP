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


@pytest.mark.asyncio
async def test_safety_stock_no_tenant(client):
    response = await client.post(
        "/api/v1/material/safety-stock",
        json={"avg_daily_demand": 100, "demand_std_dev": 20, "avg_lead_time_days": 7, "lead_time_std_dev": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == "NO_TENANT"


@pytest.mark.asyncio
async def test_safety_stock_with_params(client):
    response = await client.post(
        "/api/v1/material/safety-stock",
        json={
            "avg_daily_demand": 100,
            "demand_std_dev": 20,
            "avg_lead_time_days": 7,
            "lead_time_std_dev": 2,
            "service_level": 0.95,
        },
        headers={"X-Tenant-ID": TENANT_ID},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["safety_stock_qty"] > 0
    assert data["data"]["service_level"] == 0.95


@pytest.mark.asyncio
async def test_safety_stock_missing_params(client):
    response = await client.post(
        "/api/v1/material/safety-stock",
        json={},
        headers={"X-Tenant-ID": TENANT_ID},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == "MISSING_PARAMS"


@pytest.mark.asyncio
async def test_bulk_safety_stock_no_tenant(client):
    response = await client.post(
        "/api/v1/material/safety-stock/bulk",
        json={"products": []},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == "NO_TENANT"


@pytest.mark.asyncio
async def test_bulk_safety_stock(client):
    response = await client.post(
        "/api/v1/material/safety-stock/bulk",
        json={
            "products": [
                {"product_id": "P001", "avg_daily_demand": 100, "demand_std_dev": 20, "avg_lead_time_days": 7, "lead_time_std_dev": 2},
            ],
            "service_level": 0.95,
        },
        headers={"X-Tenant-ID": TENANT_ID},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["safety_stock"]) == 1


@pytest.mark.asyncio
async def test_po_suggestions_no_tenant(client):
    response = await client.post(
        "/api/v1/material/po-suggestions",
        json={"shortages": []},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == "NO_TENANT"


@pytest.mark.asyncio
async def test_po_suggestions(client):
    response = await client.post(
        "/api/v1/material/po-suggestions",
        json={
            "shortages": [
                {
                    "product_id": "P001",
                    "component_name": "Widget A",
                    "shortage_qty": 100,
                    "avg_daily_demand": 10,
                    "required_date": "2026-07-01",
                }
            ],
            "suppliers": {
                "P001": {
                    "supplier_id": "S001",
                    "supplier_name": "Acme Parts",
                    "lead_time_days": 7,
                    "lead_time_std_dev": 1,
                    "unit_cost": 25.0,
                }
            },
        },
        headers={"X-Tenant-ID": TENANT_ID},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total_suggestions"] == 1
    assert data["data"]["total_cost"] > 0
