"""Admin Copilot audit list/detail/export. Admin role only."""

from __future__ import annotations

import csv
import io
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/governance/copilot-audit", tags=["governance"])


@router.get("")
async def list_audit(
    start: str | None = None,
    end: str | None = None,
    mode: str | None = None,
    user_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(require_roles(["admin"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant")
    await db.execute(text("SELECT set_config('app.current_tenant_id', :tid, false)"), {"tid": tenant_id})
    sql = "SELECT query_id, created_at, user_id, query_mode, left(query_text,100) AS q, left(response_text,100) AS r, jsonb_array_length(response_sources) AS sources FROM cdm_copilot_audit WHERE tenant_id = CAST(:tid AS uuid)"
    params: dict = {"tid": tenant_id}
    if mode:
        sql += " AND query_mode = :mode"
        params["mode"] = mode
    if user_id:
        sql += " AND user_id = :uid"
        params["uid"] = user_id
    if start:
        sql += " AND created_at >= CAST(:start AS timestamptz)"
        params["start"] = start
    if end:
        sql += " AND created_at <= CAST(:end AS timestamptz)"
        params["end"] = end
    sql += " ORDER BY created_at DESC LIMIT 200"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return APIResponse(success=True, data={"rows": [dict(r) for r in rows]}, error=None)


@router.get("/export")
async def export_audit(
    db: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(require_roles(["admin"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant")
    await db.execute(text("SELECT set_config('app.current_tenant_id', :tid, false)"), {"tid": tenant_id})
    rows = (
        await db.execute(
            text(
                "SELECT query_id, created_at, user_id, query_mode, query_text, response_text FROM cdm_copilot_audit WHERE tenant_id = CAST(:tid AS uuid) ORDER BY created_at DESC LIMIT 5000"
            ),
            {"tid": tenant_id},
        )
    ).mappings().all()
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["query_id", "created_at", "user_id", "query_mode", "query_text", "response_text"])
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k) for k in w.fieldnames})
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv")


@router.get("/{query_id}")
async def get_audit(
    query_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(require_roles(["admin"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant")
    await db.execute(text("SELECT set_config('app.current_tenant_id', :tid, false)"), {"tid": tenant_id})
    row = (
        await db.execute(
            text("SELECT * FROM cdm_copilot_audit WHERE tenant_id = CAST(:tid AS uuid) AND query_id = CAST(:qid AS uuid)"),
            {"tid": tenant_id, "qid": str(query_id)},
        )
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return APIResponse(success=True, data=dict(row), error=None)
