"""S&OP report API (Sprint S11)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.sop_report import build_sop_report, report_to_dict
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.sop_report import SopReport
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/reports", tags=["reports"])


class SopReportCreateRequest(BaseModel):
    report_name: str = Field(default="S&OP Executive Summary")
    horizon_weeks: int = Field(default=12, ge=4, le=52)


@router.post("/sop")
async def create_sop_report(
    body: SopReportCreateRequest,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner", "manager", "executive"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    generated_by = getattr(current_user, "sub", None) or getattr(current_user, "user_id", None)
    report = await build_sop_report(
        session,
        UUID(tenant_id),
        settings.DPE_SVC_URL,
        body.report_name,
        body.horizon_weeks,
        str(generated_by) if generated_by else None,
    )
    await session.commit()
    return APIResponse(success=True, data=report_to_dict(report), error=None)


@router.get("/sop")
async def list_sop_reports(
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner", "manager", "executive"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    stmt = (
        select(SopReport)
        .where(SopReport.tenant_id == UUID(tenant_id))
        .order_by(SopReport.generated_at.desc())
        .limit(limit)
    )
    reports = (await session.execute(stmt)).scalars().all()
    return APIResponse(
        success=True,
        data={"reports": [report_to_dict(r) for r in reports], "count": len(reports)},
        error=None,
    )


@router.get("/sop/{report_id}")
async def get_sop_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner", "manager", "executive"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    report = (
        await session.execute(
            select(SopReport).where(
                SopReport.id == report_id,
                SopReport.tenant_id == UUID(tenant_id),
            )
        )
    ).scalar_one_or_none()
    if not report:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Report not found"})

    return APIResponse(success=True, data=report_to_dict(report), error=None)
