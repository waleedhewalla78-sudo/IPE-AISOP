import pytest

PRODUCT_ID = "11111111-1111-1111-1111-111111111111"


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["service"] == "order-svc"


@pytest.mark.asyncio
async def test_list_orders_empty(client, auth_headers):
    r = await client.get("/api/v1/orders", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["data"]["orders"] == []


@pytest.mark.asyncio
async def test_create_order(client, auth_headers):
    r = await client.post(
        "/api/v1/orders",
        json={
            "priority": 2,
            "lines": [{"product_id": PRODUCT_ID, "quantity": 5, "unit_price": 10}],
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["order_number"].startswith("SO-")
