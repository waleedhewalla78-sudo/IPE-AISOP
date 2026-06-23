"""Tests for scenario sandbox endpoints."""

import pytest


@pytest.mark.asyncio
async def test_clone_no_tenant(client):
    response = await client.post(
        "/api/v1/scenarios/clone",
        json={"mo_ids": [], "name": "Test"},
    )
    assert response.status_code == 200
    assert response.json()["error"]["code"] == "NO_TENANT"


@pytest.mark.asyncio
async def test_disruption_no_tenant(client):
    from uuid import uuid4
    response = await client.post(
        f"/api/v1/scenarios/{uuid4()}/disruption",
        json={"disruptions": []},
    )
    assert response.status_code == 200
    assert response.json()["error"]["code"] == "NO_TENANT"


@pytest.mark.asyncio
async def test_solve_no_tenant(client):
    from uuid import uuid4
    response = await client.post(
        f"/api/v1/scenarios/{uuid4()}/solve",
        json={},
    )
    assert response.status_code == 200
    assert response.json()["error"]["code"] == "NO_TENANT"


@pytest.mark.asyncio
async def test_diff_no_tenant(client):
    from uuid import uuid4
    response = await client.get(
        f"/api/v1/scenarios/{uuid4()}/diff",
    )
    assert response.status_code == 200
    assert response.json()["error"]["code"] == "NO_TENANT"


@pytest.mark.asyncio
async def test_clone_invalid_uuid(client):
    response = await client.post(
        "/api/v1/scenarios/clone",
        json={"mo_ids": ["not-a-uuid"], "name": "Test"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_disruption_invalid_uuid(client):
    response = await client.post(
        "/api/v1/scenarios/not-a-uuid/disruption",
        json={"disruptions": []},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_solve_invalid_uuid(client):
    response = await client.post(
        "/api/v1/scenarios/not-a-uuid/solve",
        json={},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_diff_invalid_uuid(client):
    response = await client.get(
        "/api/v1/scenarios/not-a-uuid/diff",
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unauthorized_role_returns_403(rbac_client):
    from uuid import uuid4
    from ipe_shared.auth.jwt import create_access_token
    token = create_access_token(
        user_id=uuid4(),
        tenant_id=uuid4(),
        role="auditor",
    )
    response = await rbac_client.post(
        f"/api/v1/scenarios/{uuid4()}/solve",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
