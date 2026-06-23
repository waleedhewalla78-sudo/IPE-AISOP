from uuid import UUID

from fastapi import APIRouter, Depends, Query

from ipe_shared.auth.jwt import create_access_token
from ipe_shared.auth.dependencies import get_current_user
from ipe_shared.compliance.gdpr import DSARService, DSARType, DSARStatus

router = APIRouter(prefix="/dsar", tags=["GDPR DSAR"])
_dsar_service = DSARService()


@router.post("/requests", status_code=201)
async def create_dsar_request(
    subject_email: str,
    request_type: DSARType,
    description: str = "",
    tenant_id: UUID = Query(...),
    current_user: dict = Depends(get_current_user),
):
    request = _dsar_service.create_request(
        tenant_id=str(tenant_id),
        subject_email=subject_email,
        request_type=request_type,
        description=description,
    )
    return {"success": True, "data": request.to_dict()}


@router.get("/requests")
async def list_dsar_requests(
    tenant_id: UUID | None = None,
    status: DSARStatus | None = None,
    current_user: dict = Depends(get_current_user),
):
    requests = _dsar_service.list_requests(
        tenant_id=str(tenant_id) if tenant_id else None,
        status=status,
    )
    return {
        "success": True,
        "data": {"requests": [r.to_dict() for r in requests], "total": len(requests)},
    }


@router.get("/requests/{request_id}")
async def get_dsar_request(
    request_id: str,
    current_user: dict = Depends(get_current_user),
):
    request = _dsar_service.get_request(request_id)
    if not request:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "DSAR request not found"}}
    return {"success": True, "data": request.to_dict()}


@router.post("/requests/{request_id}/process")
async def start_processing(
    request_id: str,
    current_user: dict = Depends(get_current_user),
):
    request = _dsar_service.start_processing(request_id)
    if not request:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "DSAR request not found"}}
    return {"success": True, "data": request.to_dict()}


@router.post("/requests/{request_id}/complete")
async def complete_dsar_request(
    request_id: str,
    current_user: dict = Depends(get_current_user),
):
    request = _dsar_service.complete_request(request_id)
    if not request:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "DSAR request not found"}}
    return {"success": True, "data": request.to_dict()}


@router.post("/requests/{request_id}/deny")
async def deny_dsar_request(
    request_id: str,
    reason: str,
    current_user: dict = Depends(get_current_user),
):
    request = _dsar_service.deny_request(request_id, reason=reason)
    if not request:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "DSAR request not found"}}
    return {"success": True, "data": request.to_dict()}


@router.get("/data-mapping")
async def get_data_mapping(
    current_user: dict = Depends(get_current_user),
):
    return {"success": True, "data": _dsar_service.get_subject_data_mapping()}