"""Upload + wizard API endpoints."""

from __future__ import annotations

import io
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, File, Header, UploadFile
from fastapi.responses import StreamingResponse
from openpyxl import Workbook

from app.core.validator import UploadValidator, normalize_file_type
from app.core.wizard import wizard_store

router = APIRouter(prefix="/upload", tags=["upload"])
_validator = UploadValidator()
_upload_store: dict[str, dict[str, Any]] = {}


def _tenant(x_tenant_id: str | None) -> str:
    return x_tenant_id or "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"


@router.get("/wizard/status")
async def wizard_status(x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    return wizard_store.status(_tenant(x_tenant_id))


@router.post("/wizard/complete-phase/{phase_number}")
async def complete_phase(
    phase_number: int,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    return wizard_store.complete_phase(_tenant(x_tenant_id), phase_number)


@router.get("/templates")
async def list_templates():
    from app.core.validator import FILE_SCHEMAS

    return {
        "templates": [
            {"file_type": k, "required_columns": v["required"], "phase": v["phase"]}
            for k, v in FILE_SCHEMAS.items()
        ]
    }


@router.post("/{file_type}")
async def upload_file(
    file_type: str,
    file: UploadFile = File(...),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    tenant = _tenant(x_tenant_id)
    content = await file.read()
    result = _validator.validate(file_type, content, file.filename or f"{file_type}.csv")
    upload_id = str(uuid4())
    ft = normalize_file_type(file_type)
    if result.accepted > 0 or result.stage_1_structure.get("status") == "pass":
        wizard_store.record_upload(tenant, ft)

    payload = {
        "upload_id": upload_id,
        "file_type": ft,
        "file_name": file.filename,
        "validation": {
            "stage_1_structure": result.stage_1_structure,
            "stage_2_types": result.stage_2_types,
            "stage_3_referential": result.stage_3_referential,
            "stage_4_business": result.stage_4_business,
        },
        "result": {
            "total_rows": result.total_rows,
            "accepted": result.accepted,
            "rejected": result.rejected,
            "warnings": result.warnings,
        },
        "agents_triggered": result.agents_triggered,
        "agent_results_eta": "~30 seconds",
        "download_errors_url": f"/api/v1/upload/{upload_id}/errors.xlsx",
    }
    _upload_store[upload_id] = {"errors": result.errors, "payload": payload}
    return payload


@router.get("/{upload_id}/errors.xlsx")
async def download_errors(upload_id: str):
    stored = _upload_store.get(upload_id)
    if not stored:
        return {"error": "upload not found"}
    wb = Workbook()
    ws = wb.active
    ws.title = "errors"
    ws.append(["row", "column", "value", "message", "severity"])
    for e in stored["errors"]:
        ws.append([e.row, e.column, e.value, e.message, e.severity])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="upload-{upload_id}-errors.xlsx"'},
    )
