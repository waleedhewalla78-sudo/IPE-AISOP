"""DQ API — include from dpe-svc router when that file is clean."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.data_quality.catalog import CATALOG
from app.data_quality.engine import run_all_checks
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/data-quality", tags=["data-quality"])


@router.post("/run")
async def run_dq(
    db: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(require_roles(["admin"])),
):
    from uuid import UUID

    tid = tenant_ctx.get()
    if not tid:
        raise HTTPException(400, "No tenant")
    report = await run_all_checks(db, UUID(tid))
    return APIResponse(
        success=True,
        data={"report_id": report.report_id, "score": report.score, "checks": len(report.checks)},
        error=None,
    )


@router.get("/catalog")
async def catalog(_: TokenPayload = Depends(require_roles(["admin"]))):
    return APIResponse(
        success=True,
        data=[{"id": c.id, "entity": c.entity, "severity": c.severity, "fix": c.fix_guidance} for c in CATALOG],
        error=None,
    )
