"""ERP connections REST API (W1-04 Sprint 4)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

from app.core import erp_connections_service as svc
from app.schemas.erp_connections import (
    ErpConnectionCreate,
    ErpConnectionLogEntry,
    ErpConnectionTestResult,
    ErpConnectionUpdate,
    SyncNowResponse,
)
from fastapi import HTTPException

router = APIRouter(prefix="/erp/connections", tags=["erp-connections"])


def _tenant_uuid() -> UUID:
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "NO_TENANT", "message": "No tenant context"},
        )
    return UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_connection(
    req: ErpConnectionCreate,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["admin"])),
):
    tid = _tenant_uuid()
    data = await svc.create_connection(session, tid, req)
    return APIResponse(success=True, data=data.model_dump(mode="json"), error=None)


@router.get("")
async def list_connections(session: AsyncSession = Depends(get_db_session)):
    tid = _tenant_uuid()
    rows = await svc.list_connections(session, tid)
    return APIResponse(
        success=True,
        data=[r.model_dump(mode="json") for r in rows],
        error=None,
    )


@router.get("/{connection_id}")
async def get_connection(connection_id: UUID, session: AsyncSession = Depends(get_db_session)):
    tid = _tenant_uuid()
    row = await svc.get_connection(session, tid, connection_id)
    return APIResponse(success=True, data=svc.to_response(row).model_dump(mode="json"), error=None)


@router.put("/{connection_id}")
async def update_connection(
    connection_id: UUID,
    req: ErpConnectionUpdate,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["admin"])),
):
    tid = _tenant_uuid()
    data = await svc.update_connection(session, tid, connection_id, req)
    return APIResponse(success=True, data=data.model_dump(mode="json"), error=None)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["admin"])),
):
    tid = _tenant_uuid()
    await svc.soft_delete_connection(session, tid, connection_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{connection_id}/test")
async def test_connection(
    connection_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["admin"])),
):
    tid = _tenant_uuid()
    result = await svc.test_connection(session, tid, connection_id)
    return APIResponse(
        success=True,
        data=ErpConnectionTestResult(**result).model_dump(),
        error=None,
    )


@router.post("/{connection_id}/activate")
async def activate_connection(
    connection_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["admin"])),
):
    tid = _tenant_uuid()
    data = await svc.activate_connection(session, tid, connection_id)
    return APIResponse(success=True, data=data.model_dump(mode="json"), error=None)


@router.get("/{connection_id}/logs")
async def get_connection_logs(
    connection_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    action: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
):
    tid = _tenant_uuid()
    logs = await svc.list_logs(session, tid, connection_id, limit=limit, action=action)
    return APIResponse(
        success=True,
        data=[ErpConnectionLogEntry.model_validate(x).model_dump(mode="json") for x in logs],
        error=None,
    )


@router.post("/{connection_id}/sync-now")
async def sync_now(
    connection_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["admin"])),
):
    tid = _tenant_uuid()
    result = await svc.sync_now(session, tid, connection_id)
    return APIResponse(
        success=True,
        data=SyncNowResponse(**result).model_dump(mode="json"),
        error=None,
    )
