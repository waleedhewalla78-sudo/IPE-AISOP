from contextvars import ContextVar
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from ipe_shared.auth.jwt import decode_token

logger = logging.getLogger(__name__)

tenant_ctx: ContextVar[str] = ContextVar("tenant_id", default=None)


class TenantContextMiddleware(BaseHTTPMiddleware):
    EXCLUDED_PATHS = {
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/health",
        "/api/v1/ready",
        "/api/v1/auth/login",
        "/metrics",
        "/health",
        "/ready",
    }

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        token_ref = None
        if token:
            try:
                payload = decode_token(token)
                token_ref = tenant_ctx.set(str(payload.tenant_id))
            except Exception as e:
                logger.warning("JWT decode failed: %s", e)

        if not tenant_ctx.get():
            tenant_id = request.headers.get("X-Tenant-ID")
            if tenant_id:
                token_ref = tenant_ctx.set(str(tenant_id))

        try:
            return await call_next(request)
        finally:
            if token_ref:
                tenant_ctx.reset(token_ref)
