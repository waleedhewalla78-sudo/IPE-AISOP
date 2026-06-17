from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from ipe_shared.auth.jwt import decode_token

tenant_ctx: ContextVar[str] = ContextVar("tenant_id", default=None)


class TenantContextMiddleware(BaseHTTPMiddleware):
    EXCLUDED_PATHS = {"/docs", "/redoc", "/openapi.json", "/api/v1/health", "/api/v1/ready"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        token_ref = None
        if token:
            try:
                payload = decode_token(token)
                token_ref = tenant_ctx.set(str(payload.tenant_id))
            except Exception:
                pass

        if not tenant_ctx.get():
            tenant_id = request.headers.get("X-Tenant-ID")
            if tenant_id:
                token_ref = tenant_ctx.set(str(tenant_id))

        try:
            return await call_next(request)
        finally:
            if token_ref:
                tenant_ctx.reset(token_ref)
