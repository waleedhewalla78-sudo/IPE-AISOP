"""Master Data Readiness dashboard API."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.mdr_engine import calculate_mdr, detect_routing_deviation
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/demand/mdr", tags=["mdr"])


@router.get("/dashboard")
async def mdr_dashboard(
    session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager"])),
) -> APIResponse:
    result = await calculate_mdr(session)
    if result.get("error"):
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": result["error"]})
    return APIResponse(success=True, data=result, error=None)


@router.get("/routing-deviations")
async def routing_deviations(
    session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager"])),
) -> APIResponse:
    """Return routing correction drafts for operations with ≥15% deviation."""
    drafts = await detect_routing_deviation(session)
    return APIResponse(success=True, data={"drafts": drafts, "count": len(drafts)}, error=None)
