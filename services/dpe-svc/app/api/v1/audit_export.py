"""Audit log export API — CSV download for compliance officers."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.audit.export import archive_audit_csv_to_minio, audit_rows_to_csv, fetch_audit_rows
from ipe_shared.auth.dependencies import get_current_user, get_tenant_id
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/audit/export", response_model=None)
async def export_audit_log(
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    format: str = Query("csv", pattern="^(csv|json)$"),
    archive: bool = Query(False, description="Also write CSV to MinIO when configured"),
    session: AsyncSession = Depends(get_session),
    tenant_id=Depends(get_tenant_id),
    current_user: TokenPayload = Depends(require_roles(["admin", "auditor"])),
) -> PlainTextResponse | APIResponse:
    rows = await fetch_audit_rows(session, str(tenant_id), start=start, end=end)
    if format == "json":
        return APIResponse(success=True, data={"count": len(rows), "rows": rows}, error=None)

    csv_content = audit_rows_to_csv(rows)
    if archive:
        stamp = datetime.utcnow().strftime("%Y%m%d")
        await archive_audit_csv_to_minio(csv_content, f"audit-{tenant_id}-{stamp}.csv")

    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="audit-{tenant_id}.csv"'},
    )
