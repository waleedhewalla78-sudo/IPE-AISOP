"""POST /api/v1/data/upload — Star Trans multi-sheet Excel ingestion (Stream 2)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.startrans_ingest import ingest_workbook
from app.core.startrans_workbook import parse_workbook, preview_counts
from ipe_shared.database.session import get_session

router = APIRouter(prefix="/data", tags=["data-upload"])

_workbook_store: dict[str, dict[str, Any]] = {}


class DataCommitRequest(BaseModel):
    upload_id: str = Field(..., min_length=1)
    dry_run: bool = False


def _tenant(x_tenant_id: str | None) -> str:
    return x_tenant_id or "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"


@router.post("/upload")
async def upload_startrans_workbook(
    files: list[UploadFile] = File(...),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    """Accept one or more .xlsx files; validate sheet names; return preview."""
    if not files:
        raise HTTPException(status_code=400, detail="At least one .xlsx file required")

    tenant = _tenant(x_tenant_id)
    results: list[dict[str, Any]] = []

    for f in files:
        content = await f.read()
        parsed = parse_workbook(content, f.filename or "workbook.xlsx")
        preview = preview_counts(parsed)
        upload_id = str(uuid4())
        _workbook_store[upload_id] = {
            "tenant_id": tenant,
            "file_name": f.filename,
            "content": content,
            "parsed": parsed,
            "preview": preview,
        }
        results.append(
            {
                "upload_id": upload_id,
                "file_name": f.filename,
                "valid": parsed.valid,
                "sheets_found": parsed.sheets_found,
                "sheets_missing": parsed.sheets_missing,
                "sheets_extra": parsed.sheets_extra,
                "errors": parsed.errors,
                "preview": {
                    "will_insert": preview["will_insert"],
                    "will_fail": preview["will_fail"],
                    "sheets": preview["sheets"],
                },
            }
        )

    return {
        "count": len(results),
        "uploads": results,
        "message": (
            f"{sum(u['preview']['will_insert'] for u in results)} rows will insert, "
            f"{sum(u['preview']['will_fail'] for u in results)} rows will fail"
        ),
    }


@router.post("/upload/commit")
async def commit_startrans_workbook(
    body: DataCommitRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_session),
):
    tenant = _tenant(x_tenant_id)
    stored = _workbook_store.get(body.upload_id)
    if not stored:
        raise HTTPException(status_code=400, detail="Unknown or expired upload_id — re-upload first")
    if stored.get("tenant_id") != tenant:
        raise HTTPException(status_code=400, detail="upload_id does not belong to this tenant")

    parsed = stored["parsed"]
    result = await ingest_workbook(session, parsed, dry_run=body.dry_run)
    return {
        "upload_id": body.upload_id,
        "file_name": stored.get("file_name"),
        **result,
    }


@router.get("/upload/expected-sheets")
async def expected_sheets():
    from app.core.startrans_workbook import EXPECTED_SHEETS, NATURAL_KEYS

    return {
        "count": len(EXPECTED_SHEETS),
        "sheets": [
            {"name": s, "natural_key": NATURAL_KEYS.get(s)} for s in EXPECTED_SHEETS
        ],
    }
