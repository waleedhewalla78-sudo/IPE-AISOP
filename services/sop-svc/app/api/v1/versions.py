from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import delete as sa_delete
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.version import compare_totals
from app.schemas.version import SopVersionCreateRequest
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.planning_intelligence import ConsensusDemand, SopVersion
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/sop/version", tags=["sop-version"])
SOP_ROLES = ["admin", "planner", "manager", "executive"]


def _tenant_uuid() -> UUID | None:
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return None
    return UUID(str(tenant_id))


def _user_uuid(user: TokenPayload) -> UUID | None:
    try:
        return UUID(str(user.sub))
    except Exception:
        return None


def _no_tenant() -> APIResponse:
    return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})


def _version_to_dict(version: SopVersion) -> dict:
    return {
        "id": str(version.id),
        "cycle_id": str(version.cycle_id),
        "version_type": version.version_type,
        "version_name": version.version_name,
        "description": version.description,
        "is_active": bool(version.is_active),
        "created_by": str(version.created_by) if version.created_by else None,
        "created_at": version.created_at.isoformat() if version.created_at else None,
    }


@router.post("")
async def create_version(
    req: SopVersionCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager"])),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    version = SopVersion(
        tenant_id=tenant_id,
        cycle_id=req.cycle_id,
        version_type=req.version_type,
        version_name=req.version_name,
        description=req.description,
        is_active=req.is_active,
        created_by=_user_uuid(current_user),
    )
    session.add(version)
    await session.flush()
    await session.commit()
    return APIResponse(success=True, data=_version_to_dict(version), error=None)


@router.get("/compare")
async def compare_versions(
    version_a_id: UUID,
    version_b_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(SOP_ROLES)),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    base_rows = (
        await session.execute(
            sa_select(ConsensusDemand).where(
                ConsensusDemand.tenant_id == tenant_id,
                ConsensusDemand.version_id == version_a_id,
            )
        )
    ).scalars().all()
    compare_rows = (
        await session.execute(
            sa_select(ConsensusDemand).where(
                ConsensusDemand.tenant_id == tenant_id,
                ConsensusDemand.version_id == version_b_id,
            )
        )
    ).scalars().all()
    return APIResponse(success=True, data=compare_totals(base_rows, compare_rows), error=None)


@router.delete("/{version_id}")
async def delete_version(
    version_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(["admin", "planner", "manager"])),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    result = await session.execute(
        sa_delete(SopVersion).where(SopVersion.tenant_id == tenant_id, SopVersion.id == version_id)
    )
    await session.commit()
    deleted = int(result.rowcount or 0)
    if deleted == 0:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "S&OP version not found"})
    return APIResponse(success=True, data={"deleted": deleted, "version_id": str(version_id)}, error=None)
