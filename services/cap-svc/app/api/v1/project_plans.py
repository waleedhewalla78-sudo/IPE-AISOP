"""Project plan upload, version management, and schedule export."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.project_plan_parser import ProjectPlanParseError, parse_project_plan_excel
from app.core.project_plan_schema import schema_documentation
from app.core.project_plan_service import (
    ProjectPlanServiceError,
    activate_version,
    get_active_schedule,
    get_plan_by_code,
    list_plans,
    list_versions,
    upload_plan_version,
)
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/capacity/project-plans", tags=["project-plans"])


@router.get("/schema")
async def get_excel_schema(
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager"])),
) -> APIResponse:
    """Return machine-readable Excel schema for clients and documentation tools."""
    return APIResponse(success=True, data=schema_documentation(), error=None)


@router.get("")
async def get_project_plans(
    session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager", "supervisor"])),
) -> APIResponse:
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})
    plans = await list_plans(session, UUID(tenant_id))
    return APIResponse(success=True, data={"plans": plans}, error=None)


@router.get("/{plan_code}/versions")
async def get_plan_versions(
    plan_code: str,
    session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager", "supervisor"])),
) -> APIResponse:
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})
    try:
        versions = await list_versions(session, UUID(tenant_id), plan_code)
    except ProjectPlanServiceError as exc:
        return APIResponse(success=False, data=None, error={"code": exc.code, "message": exc.message})
    return APIResponse(success=True, data={"plan_code": plan_code, "versions": versions}, error=None)


@router.get("/{plan_code}/schedule")
async def get_plan_schedule(
    plan_code: str,
    session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager", "supervisor"])),
) -> APIResponse:
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})
    try:
        schedule = await get_active_schedule(session, UUID(tenant_id), plan_code)
    except ProjectPlanServiceError as exc:
        return APIResponse(success=False, data=None, error={"code": exc.code, "message": exc.message})
    return APIResponse(success=True, data=schedule, error=None)


@router.post("/upload")
async def upload_project_plan(
    file: UploadFile = File(...),
    mode: str = Form(...),
    plan_code: str | None = Form(None),
    notes: str | None = Form(None),
    session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager"])),
) -> APIResponse:
    """Upload Excel project plan. mode=new creates a plan; mode=update adds a version."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    normalized_mode = mode.strip().lower()
    if normalized_mode not in {"new", "update"}:
        return APIResponse(
            success=False,
            data=None,
            error={"code": "INVALID_MODE", "message": "mode must be 'new' or 'update'"},
        )

    content = await file.read()
    file_name = file.filename or "upload.xlsx"

    try:
        parsed = parse_project_plan_excel(file_name, content)
    except ProjectPlanParseError as exc:
        return APIResponse(
            success=False,
            data={"errors": exc.errors},
            error={"code": "VALIDATION_ERROR", "message": str(exc)},
        )

    if plan_code and parsed["plan_code"].lower() != plan_code.strip().lower():
        return APIResponse(
            success=False,
            data=None,
            error={
                "code": "PLAN_CODE_MISMATCH",
                "message": (
                    f"Form plan_code '{plan_code}' does not match Excel PLAN_CODE "
                    f"'{parsed['plan_code']}'"
                ),
            },
        )

    try:
        result = await upload_plan_version(
            session,
            UUID(tenant_id),
            UUID(str(current_user.sub)),
            parsed,
            file_name,
            normalized_mode,
            notes,
        )
    except ProjectPlanServiceError as exc:
        return APIResponse(success=False, data=None, error={"code": exc.code, "message": exc.message})

    return APIResponse(success=True, data=result, error=None)


@router.post("/{plan_code}/versions/{version_id}/activate")
async def activate_plan_version(
    plan_code: str,
    version_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager"])),
) -> APIResponse:
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})
    try:
        result = await activate_version(session, UUID(tenant_id), plan_code, version_id)
    except ProjectPlanServiceError as exc:
        return APIResponse(success=False, data=None, error={"code": exc.code, "message": exc.message})
    return APIResponse(success=True, data=result, error=None)


@router.get("/{plan_code}")
async def get_project_plan(
    plan_code: str,
    session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager", "supervisor"])),
) -> APIResponse:
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})
    plan = await get_plan_by_code(session, UUID(tenant_id), plan_code)
    if not plan:
        return APIResponse(
            success=False,
            data=None,
            error={"code": "NOT_FOUND", "message": f"Plan '{plan_code}' not found"},
        )
    versions = await list_versions(session, UUID(tenant_id), plan_code)
    return APIResponse(
        success=True,
        data={"plan_code": plan_code, "versions": versions},
        error=None,
    )
