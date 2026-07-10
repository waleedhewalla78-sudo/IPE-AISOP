"""Admin Odoo Config v2 API (W1-03–05)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

from app.core import odoo_config_service as svc
from app.schemas.odoo_config_v2 import (
    OdooConfigCreateRequest,
    OdooConfigListResponse,
    OdooConfigTestRequest,
    OdooConnectionTestResult,
)

router = APIRouter(prefix="/admin/odoo-config", tags=["admin-odoo-config"])


def _tenant_uuid() -> UUID:
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "NO_TENANT", "message": "No tenant context"},
        )
    return UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id


@router.get("")
async def list_odoo_configs(session: AsyncSession = Depends(get_db_session)):
    tid = _tenant_uuid()
    entities = await svc.list_current_configs(session, tid)
    return APIResponse(
        success=True,
        data=OdooConfigListResponse(entities=entities).model_dump(),
        error=None,
    )


@router.post("/test-connection")
async def test_odoo_config_connection(
    req: OdooConfigTestRequest,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["admin"])),
):
    tid = _tenant_uuid()
    result = await svc.test_odoo_connection(session, tid, req)
    return APIResponse(
        success=True,
        data=OdooConnectionTestResult(**result).model_dump(),
        error=None,
    )


@router.post("")
async def create_odoo_config(
    req: OdooConfigCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["admin"])),
):
    tid = _tenant_uuid()
    summary = await svc.create_config_version(session, tid, req)
    return APIResponse(success=True, data=summary.model_dump(), error=None)


@router.get("/{entity_key}/versions")
async def list_odoo_config_versions(
    entity_key: str,
    session: AsyncSession = Depends(get_db_session),
):
    tid = _tenant_uuid()
    versions = await svc.list_versions(session, tid, entity_key)
    return APIResponse(
        success=True,
        data={"entity_key": entity_key, "versions": [v.model_dump() for v in versions]},
        error=None,
    )


@router.post("/{entity_key}/rollback/{version}")
async def rollback_odoo_config(
    entity_key: str,
    version: int,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["admin"])),
):
    if version < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_VERSION", "message": "Version must be >= 1"},
        )
    tid = _tenant_uuid()
    summary = await svc.rollback_config(session, tid, entity_key, version)
    return APIResponse(success=True, data=summary.model_dump(), error=None)


@router.get("/{entity_key}")
async def get_odoo_config(entity_key: str, session: AsyncSession = Depends(get_db_session)):
    tid = _tenant_uuid()
    row = await svc.get_current_config(session, tid, entity_key)
    if not row:
        return APIResponse(
            success=False,
            data=None,
            error={"code": "NOT_FOUND", "message": f"No config for entity '{entity_key}'"},
        )
    return APIResponse(success=True, data=svc._to_summary(row).model_dump(), error=None)
