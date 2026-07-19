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
_upload_history: list[dict[str, Any]] = []


def _record_history(tenant: str, payload: dict[str, Any]) -> None:
    _upload_history.append(
        {
            "tenant_id": tenant,
            "upload_id": payload["upload_id"],
            "file_type": payload["file_type"],
            "file_name": payload.get("file_name"),
            "status": "completed" if payload["result"]["rejected"] == 0 else "completed_with_errors",
            "accepted": payload["result"]["accepted"],
            "rejected": payload["result"]["rejected"],
        }
    )


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


@router.get("/history")
async def upload_history(x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    tenant = _tenant(x_tenant_id)
    items = [h for h in _upload_history if h["tenant_id"] == tenant]
    return {"uploads": items, "count": len(items)}


@router.get("/templates/{file_type}")
async def download_template(file_type: str):
    from app.core.validator import FILE_SCHEMAS, normalize_file_type

    ft = normalize_file_type(file_type)
    schema = FILE_SCHEMAS.get(ft)
    if not schema:
        return {"error": f"Unknown template: {file_type}"}
    wb = Workbook()
    ws = wb.active
    ws.title = ft
    headers = list(schema["required"]) + list(schema.get("optional", []))
    ws.append(headers)
    sample = {h: f"sample_{h}" for h in headers}
    if "product_code" in sample:
        sample["product_code"] = "FG-DT100"
    if "product_type" in sample:
        sample["product_type"] = "finished"
    if "type" in sample:
        sample["type"] = "finished"
    if "short_name" in sample:
        sample["short_name"] = "DT100"
    if "full_name" in sample:
        sample["full_name"] = "Distribution Transformer 100kVA"
    if "product_group" in sample:
        sample["product_group"] = "DT"
    if "uom" in sample:
        sample["uom"] = "EA"
    if "main_storage_location" in sample:
        sample["main_storage_location"] = "WH-FG"
    ws.append([sample.get(h, "") for h in headers])
    ws.append([f"Required: {h}" if h in schema["required"] else f"Optional: {h}" for h in headers])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{ft}_template.xlsx"'},
    )


@router.get("/templates")
async def list_templates():
    from app.core.validator import FILE_SCHEMAS

    return {
        "templates": [
            {
                "file_type": k,
                "required_columns": v["required"],
                "optional_columns": v.get("optional", []),
                "phase": v["phase"],
            }
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
    _record_history(tenant, payload)
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
