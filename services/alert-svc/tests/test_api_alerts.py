import pytest

from app.api.v1.alerts import _alert_store, store_alert_from_event


@pytest.fixture(autouse=True)
def clear_alert_store():
    _alert_store.clear()
    yield
    _alert_store.clear()


@pytest.mark.asyncio
async def test_list_alerts_empty(client):
    response = await client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 0


@pytest.mark.asyncio
async def test_list_alerts_with_stored_alerts(client):
    await store_alert_from_event("ipe.mo.feasibility_scored", {
        "feasibility_score": 55,
        "mo_id": "MO-001",
        "tenant_id": "tenant-1",
        "primary_constraint": "material",
    })
    response = await client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 1
    assert data["data"]["alerts"][0]["alert_type"] == "feasibility_critical"


@pytest.mark.asyncio
async def test_get_alert_not_found(client):
    response = await client.get("/api/v1/alerts/nonexistent-id")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_get_alert_found(client):
    alerts = await store_alert_from_event("ipe.mo.feasibility_scored", {
        "feasibility_score": 40,
        "mo_id": "MO-002",
        "tenant_id": "tenant-1",
    })
    alert_id = list(_alert_store.keys())[0]
    response = await client.get(f"/api/v1/alerts/{alert_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["entity_id"] == "MO-002"


@pytest.mark.asyncio
async def test_acknowledge_alert(client):
    await store_alert_from_event("ipe.mo.feasibility_scored", {
        "feasibility_score": 50,
        "mo_id": "MO-003",
        "tenant_id": "tenant-1",
    })
    alert_id = list(_alert_store.keys())[0]
    response = await client.post(
        f"/api/v1/alerts/{alert_id}/acknowledge",
        json={"acknowledged_by": "planner-1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["acknowledged"] is True
    assert data["data"]["acknowledged_by"] == "planner-1"


@pytest.mark.asyncio
async def test_acknowledge_alert_not_found(client):
    response = await client.post("/api/v1/alerts/nonexistent/acknowledge")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_list_active_rules(client):
    response = await client.get("/api/v1/alerts/rules/active")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["rules"]) == 2


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
