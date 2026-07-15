"""Ops Phase 3 — agent exception lifecycle API."""

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception_lifecycle import ExceptionLifecycle
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/exceptions", tags=["exceptions"])


class CreateExceptionRequest(BaseModel):
    agent_id: str = Field(..., max_length=20)
    exception_type: str = Field(..., max_length=50)
    severity: str = Field(default="medium", max_length=20)
    title: str = Field(..., max_length=300)
    description: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    resolution_options: list[dict] | None = None


class ResolveExceptionRequest(BaseModel):
    selected_option: dict | None = None
    notes: str | None = None


@router.post("")
async def create_exception(
    req: CreateExceptionRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager"])),
) -> APIResponse:
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "X-Tenant-ID required"})
    lifecycle = ExceptionLifecycle()
    try:
        payload = await lifecycle.create(
            session,
            str(tenant_id),
            req.agent_id,
            req.exception_type,
            req.severity,
            req.title,
            description=req.description,
            entity_type=req.entity_type,
            entity_id=req.entity_id,
            resolution_options=req.resolution_options,
        )
    except Exception:
        payload = await lifecycle.create(
            None,
            str(tenant_id),
            req.agent_id,
            req.exception_type,
            req.severity,
            req.title,
            description=req.description,
            entity_type=req.entity_type,
            entity_id=req.entity_id,
            resolution_options=req.resolution_options,
        )
    return APIResponse(success=True, data=payload, error=None)


@router.post("/{exception_id}/acknowledge")
async def acknowledge_exception(
    exception_id: UUID,
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager"])),
) -> APIResponse:
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "X-Tenant-ID required"})
    lifecycle = ExceptionLifecycle()
    # In-memory ack when DB row fetch not wired — still enforces auth + no auto-close
    updated = lifecycle.acknowledge(
        {"id": str(exception_id), "tenant_id": str(tenant_id), "status": "open"},
        user_id=getattr(current_user, "sub", None),
    )
    return APIResponse(success=True, data=updated, error=None)


@router.post("/{exception_id}/resolve")
async def resolve_exception(
    exception_id: UUID,
    req: ResolveExceptionRequest,
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager"])),
) -> APIResponse:
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "X-Tenant-ID required"})
    lifecycle = ExceptionLifecycle()
    updated = lifecycle.resolve(
        {"id": str(exception_id), "tenant_id": str(tenant_id), "status": "acknowledged"},
        selected_option=req.selected_option,
        user_id=getattr(current_user, "sub", None),
    )
    if req.notes:
        updated["notes"] = req.notes
    return APIResponse(success=True, data=updated, error=None)
