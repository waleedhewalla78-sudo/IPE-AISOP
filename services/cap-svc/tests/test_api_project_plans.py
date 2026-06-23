"""API tests for project plan upload endpoints."""

import io
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from openpyxl import Workbook

HEADER = [
    "PLAN_CODE",
    "PLAN_NAME",
    "MO_ID",
    "OPERATION_SEQUENCE",
    "OPERATION_NAME",
    "WORK_CENTER_CODE",
    "START_HOUR",
    "DURATION_HOURS",
    "STATUS",
]


def _xlsx_bytes() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(HEADER)
    ws.append(["PLAN-DEMO-Q3", "Q3 Demo", "MO-DEMO-001", 10, "Assemble", "WC001", 0, 2, "planned"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_schema_endpoint(client, auth_headers):
    response = await client.get("/api/v1/capacity/project-plans/schema", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["schema_version"] == "1.0"
    assert any(c["name"] == "PLAN_CODE" for c in data["data"]["columns"])


@pytest.mark.asyncio
async def test_upload_validation_error(client, auth_headers):
    files = {"file": ("bad.txt", b"not excel", "text/plain")}
    data = {"mode": "new"}
    response = await client.post(
        "/api/v1/capacity/project-plans/upload",
        headers=auth_headers,
        files=files,
        data=data,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_upload_success(client, auth_headers):
    mock_result = {
        "message": "Plan 'PLAN-DEMO-Q3' version 1 uploaded successfully.",
        "plan": {"plan_code": "PLAN-DEMO-Q3", "active_version_number": 1},
        "version": {"version_number": 1, "is_active": True},
    }
    with patch(
        "app.api.v1.project_plans.upload_plan_version",
        new=AsyncMock(return_value=mock_result),
    ):
        files = {
            "file": (
                "plan.xlsx",
                _xlsx_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }
        data = {"mode": "new", "notes": "demo upload"}
        response = await client.post(
            "/api/v1/capacity/project-plans/upload",
            headers=auth_headers,
            files=files,
            data=data,
        )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "PLAN-DEMO-Q3" in body["data"]["message"]


@pytest.mark.asyncio
async def test_upload_requires_auth(rbac_client):
    files = {"file": ("plan.xlsx", _xlsx_bytes(), "application/octet-stream")}
    response = await rbac_client.post(
        "/api/v1/capacity/project-plans/upload",
        files=files,
        data={"mode": "new"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_activate_version(client, auth_headers):
    version_id = uuid4()
    mock_result = {
        "message": f"Activated version 1 for plan 'PLAN-DEMO-Q3'.",
        "plan": {"plan_code": "PLAN-DEMO-Q3", "active_version_number": 1},
    }
    with patch(
        "app.api.v1.project_plans.activate_version",
        new=AsyncMock(return_value=mock_result),
    ):
        response = await client.post(
            f"/api/v1/capacity/project-plans/PLAN-DEMO-Q3/versions/{version_id}/activate",
            headers=auth_headers,
        )
    assert response.status_code == 200
    assert response.json()["success"] is True
