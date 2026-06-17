import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ipe_shared.database.connection import get_engine
from ipe_shared.models.tenant import Tenant
from ipe_shared.schemas.common import APIResponse
from ipe_shared.middleware.tenant_context import tenant_ctx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ipe", tags=["odoo-action"])


@router.post("/action")
async def receive_odoo_action(request: Request):
    signature = request.headers.get("X-IPE-Signature", "")
    if not signature:
        return APIResponse(
            success=False, data=None,
            error={"code": "MISSING_SIGNATURE", "message": "X-IPE-Signature header is required"},
        )

    body_bytes = await request.body()

    tenant_id = request.headers.get("X-Tenant-ID", "")
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "MISSING_TENANT", "message": "X-Tenant-ID header is required"},
        )

    engine = get_engine()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        await session.execute(
            text("SET LOCAL app.current_tenant_id = :tid"),
            {"tid": tenant_id},
        )

        result = await session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()
        if not tenant:
            return APIResponse(
                success=False, data=None,
                error={"code": "NOT_FOUND", "message": "Tenant not found"},
            )

        api_secret = getattr(tenant, "api_secret", None) or ""
        if not api_secret:
            return APIResponse(
                success=False, data=None,
                error={"code": "NO_API_SECRET", "message": "Tenant has no api_secret configured"},
            )

        expected_sig = hmac.new(
            api_secret.encode(),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return APIResponse(
                success=False, data=None,
                error={"code": "INVALID_SIGNATURE", "message": "HMAC signature does not match"},
            )

        try:
            body = json.loads(body_bytes)
        except Exception:
            body = {"raw": body_bytes.decode("utf-8", errors="replace")}

        action = body.get("action", "unknown")
        logger.info("Odoo action received: %s for tenant %s", action, tenant_id)

        return APIResponse(
            success=True,
            data={"action": action, "status": "received"},
            error=None,
        )
