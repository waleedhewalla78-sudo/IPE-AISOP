from unittest.mock import AsyncMock, patch

from uuid import UUID

import pytest

from app.core.scorer import calculate_feasibility

INVALID_UUIDS = ["not-a-uuid", "123", "abc-def-ghi", "", "null", "None"]


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["service"] == "fea-svc"


@pytest.mark.asyncio
async def test_score_no_tenant(client):
    response = await client.post(
        "/api/v1/feasibility/score",
        json={"mo_id": str(UUID(int=1))},
    )
    assert response.status_code == 200
    assert response.json()["error"]["code"] == "NO_TENANT"


@pytest.mark.parametrize("bad_uuid", INVALID_UUIDS)
@pytest.mark.asyncio
async def test_score_invalid_uuid_returns_422(bad_uuid, client):
    """Prompt 1.1: Invalid UUID in mo_id is rejected by Pydantic validation."""
    response = await client.post(
        "/api/v1/feasibility/score",
        json={"mo_id": bad_uuid},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_auto_confirm_no_tenant(client):
    response = await client.post(
        "/api/v1/feasibility/auto-confirm",
        json={"mo_id": str(UUID(int=1)), "feasibility_score": 0.9, "autonomy_mode": "suggest"},
    )
    assert response.status_code == 200
    assert response.json()["error"]["code"] == "NO_TENANT"


@pytest.mark.asyncio
async def test_auto_confirm_with_auth(client, auth_headers):
    with patch("app.api.v1.feasibility.kafka_producer") as mock_kp:
        mock_kp.send_event = AsyncMock()
        response = await client.post(
            "/api/v1/feasibility/auto-confirm",
            json={"mo_id": str(UUID(int=1)), "feasibility_score": 0.9, "autonomy_mode": "suggest"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["success"] is True


@pytest.mark.parametrize("bad_uuid", INVALID_UUIDS)
@pytest.mark.asyncio
async def test_auto_confirm_invalid_uuid_returns_422(bad_uuid, client):
    """Prompt 1.1: Invalid UUID in auto-confirm is rejected."""
    with patch("app.api.v1.feasibility.kafka_producer") as mock_kp:
        mock_kp.send_event = AsyncMock()
        response = await client.post(
            "/api/v1/feasibility/auto-confirm",
            json={"mo_id": bad_uuid, "feasibility_score": 0.9, "autonomy_mode": "suggest"},
        )
        assert response.status_code == 422


def test_composite_score_calculation():
    result = calculate_feasibility(
        demand_score=100.0,
        bom_score=100.0,
        material_score=80.0,
        capacity_score=100.0,
        labor_score=100.0,
    )

    expected = 100.0 * 0.05 + 100.0 * 0.05 + 80.0 * 0.35 + 100.0 * 0.30 + 100.0 * 0.25
    expected = round(expected, 2)

    assert result["feasibility_score"] == expected
    assert result["gate_scores"]["demand"] == 100.0
    assert result["gate_scores"]["material"] == 80.0
    assert result["primary_constraint"] == "material"


def test_score_below_70_routes_to_resolution():
    result = calculate_feasibility(
        material_score=30.0,
        capacity_score=30.0,
        labor_score=30.0,
    )
    assert result["feasibility_score"] < 70.0
    assert result["action_taken"] == "routed_to_resolution"


def test_score_70_to_89_queued_for_planner():
    result = calculate_feasibility(
        material_score=80.0,
        capacity_score=80.0,
        labor_score=80.0,
    )
    score = result["feasibility_score"]
    assert 70.0 <= score < 90.0
    assert result["action_taken"] == "queued_for_planner"


def test_score_90_plus_autonomous_auto_confirms():
    result = calculate_feasibility(
        demand_score=100.0,
        bom_score=100.0,
        material_score=95.0,
        capacity_score=100.0,
        labor_score=100.0,
        autonomy_mode="autonomous",
    )
    assert result["feasibility_score"] >= 90.0
    assert result["action_taken"] == "auto_confirmed"


def test_score_90_plus_suggest_queued_for_planner():
    result = calculate_feasibility(
        demand_score=100.0,
        bom_score=100.0,
        material_score=95.0,
        capacity_score=100.0,
        labor_score=100.0,
        autonomy_mode="suggest",
    )
    assert result["feasibility_score"] >= 90.0
    assert result["action_taken"] == "queued_for_planner"
