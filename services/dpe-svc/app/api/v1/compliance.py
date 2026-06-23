from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ipe_shared.auth.dependencies import get_current_user
from ipe_shared.database.session import get_session
from ipe_shared.retention.config import get_all_policies
from ipe_shared.retention.service import RetentionService

router = APIRouter(
    prefix="/compliance/retention",
    tags=["Compliance — Retention"],
)
_retention_service = RetentionService()


class RetentionEnforceRequest(BaseModel):
    entity_type: str


class RetentionPolicyResponse(BaseModel):
    entity_type: str
    retention_days: int
    action: str
    archive_table: str | None = None


@router.post("/enforce")
async def enforce_retention(
    body: RetentionEnforceRequest,
    current_user: dict = Depends(get_current_user),
):
    async for session in get_session():
        tenant_id = (
            str(current_user.tenant_id)
            if hasattr(current_user, "tenant_id")
            else current_user.get("tenant_id")
        )
        result = await _retention_service.enforce_retention(
            session=session,
            entity_type=body.entity_type,
            tenant_id=tenant_id,
        )
        return {"success": True, "data": result}


@router.get("/policies")
async def list_retention_policies(
    current_user: dict = Depends(get_current_user),
):
    policies = get_all_policies()
    return {
        "success": True,
        "data": [
            RetentionPolicyResponse(
                entity_type=p.entity_type,
                retention_days=p.retention_days,
                action=p.action,
                archive_table=p.archive_table,
            ).model_dump()
            for p in policies.values()
        ],
    }
