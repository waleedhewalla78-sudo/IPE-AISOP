import os
os.environ.setdefault("IPE_JWT_SECRET_KEY", "dev-jwt-secret-change-in-production-min-32-chars")

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ipe_shared.config import settings
settings.JWT_SECRET_KEY = "dev-jwt-secret-change-in-production-min-32-chars"

USER_ID = UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
TENANT_ID = UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")

DB_AVAILABLE = bool(os.environ.get("IPE_DATABASE_URL_SYNC") or os.environ.get("DATABASE_URL"))
skip_if_no_db = pytest.mark.skipif(not DB_AVAILABLE, reason="Database not available")


def _auth_headers():
    from ipe_shared.auth.jwt import create_access_token
    token = create_access_token(USER_ID, TENANT_ID, "admin")
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(TENANT_ID)}


def _make_mock_session():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_scalars.one_or_none.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_result.scalar_one_or_none.return_value = None
    mock_result.fetchone.return_value = ({},)
    mock_result.fetchall.return_value = []
    mock_result.scalar.return_value = 0
    mock_session.execute = AsyncMock(return_value=mock_result)
    return mock_session


@pytest.fixture
def app_with_overrides():
    from app.main import create_app
    from ipe_shared.auth.dependencies import get_current_user
    from ipe_shared.database.session import get_session as get_db_session

    _app = create_app()

    from ipe_shared.auth.jwt import TokenPayload
    mock_user = TokenPayload(
        sub=str(USER_ID),
        tenant_id=str(TENANT_ID),
        role="admin",
    )

    async def _mock_get_current_user():
        return mock_user

    mock_session = _make_mock_session()

    async def _mock_get_session():
        yield mock_session

    _app.dependency_overrides[get_current_user] = _mock_get_current_user
    _app.dependency_overrides[get_db_session] = _mock_get_session

    yield _app

    _app.dependency_overrides.clear()


@pytest.fixture
async def client(app_with_overrides):
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app_with_overrides)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_financial_project_valid(client):
    response = await client.post(
        "/api/v1/financial/project",
        json={
            "product_id": "00000000-0000-0000-0000-000000000001",
            "quantity": 100,
            "selling_price": 150.0,
            "overhead_pct": 0.15,
            "labor_cost_per_hour": 50.0,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data


@pytest.mark.asyncio
async def test_financial_project_invalid_product_id(client):
    response = await client.post(
        "/api/v1/financial/project",
        json={
            "product_id": "not-a-uuid",
            "quantity": 100,
            "selling_price": 150.0,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_financial_project_zero_quantity(client):
    response = await client.post(
        "/api/v1/financial/project",
        json={
            "product_id": "00000000-0000-0000-0000-000000000001",
            "quantity": 0,
            "selling_price": 150.0,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.fixture
def app_no_auth():
    from app.main import create_app
    from ipe_shared.database.session import get_session as get_db_session

    _app = create_app()

    mock_session = _make_mock_session()

    async def _mock_get_session():
        yield mock_session

    _app.dependency_overrides[get_db_session] = _mock_get_session

    yield _app

    _app.dependency_overrides.clear()


@pytest.fixture
async def no_auth_client(app_no_auth):
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app_no_auth)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_financial_project_no_auth(no_auth_client):
    response = await no_auth_client.post(
        "/api/v1/financial/project",
        json={
            "product_id": "00000000-0000-0000-0000-000000000001",
            "quantity": 100,
            "selling_price": 150.0,
        },
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_financial_batch_projection(client):
    response = await client.post(
        "/api/v1/financial/project/batch",
        json={
            "projections": [
                {
                    "product_id": "00000000-0000-0000-0000-000000000001",
                    "quantity": 50,
                    "selling_price": 100.0,
                },
                {
                    "product_id": "00000000-0000-0000-0000-000000000002",
                    "quantity": 100,
                    "selling_price": 200.0,
                },
            ]
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_cost_accounting_cogm(client):
    response = await client.post(
        "/api/v1/cost-accounting/cogm",
        json={
            "material_cost": 1000.0,
            "labor_cost": 500.0,
            "energy_cost": 200.0,
            "overhead_cost": 300.0,
            "quantity": 100,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "total_cogm" in data["data"]
    assert "cogm_per_unit" in data["data"]
    assert "gl_accounts" in data["data"]


@pytest.mark.asyncio
async def test_cost_accounting_copq(client):
    response = await client.post(
        "/api/v1/cost-accounting/copq",
        json={
            "total_quantity": 1000,
            "defect_rate_pct": 2.0,
            "rework_rate_pct": 1.0,
            "inspection_cost_per_unit": 5.0,
            "warranty_cost_per_unit": 10.0,
            "standard_cost_per_unit": 100.0,
            "selling_price_per_unit": 150.0,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "total_copq" in data["data"]
    assert "copq_as_pct_of_revenue" in data["data"]


@pytest.mark.asyncio
async def test_cost_accounting_full(client):
    response = await client.post(
        "/api/v1/cost-accounting/full",
        json={
            "product_id": "P001",
            "quantity": 100,
            "selling_price": 150.0,
            "material_cost": 50.0,
            "labor_cost": 30.0,
            "energy_cost": 10.0,
            "overhead_cost": 15.0,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "cogm" in data["data"]
    assert "copq" in data["data"]
    assert "gross_margin" in data["data"]
    assert "net_margin" in data["data"]
    assert "variances" in data["data"]
    assert "xai_explanation" in data["data"]


@pytest.mark.asyncio
async def test_cost_accounting_no_auth(no_auth_client):
    response = await no_auth_client.post(
        "/api/v1/cost-accounting/cogm",
        json={
            "material_cost": 1000.0,
            "labor_cost": 500.0,
            "energy_cost": 200.0,
            "overhead_cost": 300.0,
            "quantity": 100,
        },
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_sop_forecast_ingest(client):
    response = await client.post(
        "/api/v1/sop/forecast",
        json={
            "product_family": "Widget",
            "period_type": "weekly",
            "period_start": "2026-07-01",
            "period_end": "2026-07-07",
            "forecast_qty": 500.0,
            "confidence_pct": 0.85,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["forecast_id"] is not None
    assert data["data"]["status"] == "ingested"


@pytest.mark.asyncio
async def test_sop_solve(client):
    response = await client.post(
        "/api/v1/sop/solve",
        json={
            "demand": [
                {
                    "period_start": "2026-07-01",
                    "period_end": "2026-07-07",
                    "product_family": "Widget",
                    "forecast_qty": 500.0,
                    "confidence_pct": 0.85,
                }
            ],
            "capacity": [
                {
                    "period_start": "2026-07-01",
                    "period_end": "2026-07-07",
                    "work_center_group": "Assembly",
                    "capacity_hours": 40.0,
                    "capacity_qty": 400.0,
                }
            ],
            "bottleneck_threshold_pct": 10.0,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "total_demand" in data["data"]
    assert "total_capacity" in data["data"]
    assert "bottlenecks" in data["data"]
    assert "xai_explanation" in data["data"]


@pytest.mark.asyncio
async def test_sop_solve_no_auth(no_auth_client):
    response = await no_auth_client.post(
        "/api/v1/sop/solve",
        json={
            "demand": [],
            "capacity": [],
        },
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_dsar_create_request(client):
    response = await client.post(
        "/api/v1/dsar/requests",
        params={
            "subject_email": "user@example.com",
            "request_type": "access",
            "description": "Test DSAR request",
            "tenant_id": "00000000-0000-0000-0000-000000000001",
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "request_id" in data["data"]


@pytest.mark.asyncio
async def test_dsar_list_requests(client):
    response = await client.get(
        "/api/v1/dsar/requests",
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "requests" in data["data"]


@pytest.mark.asyncio
async def test_dsar_data_mapping(client):
    response = await client.get(
        "/api/v1/dsar/data-mapping",
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
