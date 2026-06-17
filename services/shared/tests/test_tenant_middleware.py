import pytest
from unittest.mock import AsyncMock, MagicMock

from starlette.requests import Request
from starlette.responses import JSONResponse

from ipe_shared.middleware.tenant_context import TenantContextMiddleware, tenant_ctx


class TestTenantContextMiddleware:
    @pytest.fixture
    def middleware(self):
        app = AsyncMock()
        return TenantContextMiddleware(app)

    async def test_sets_tenant_ctx_when_present(self, middleware):
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/some-endpoint"
        request.headers = {"X-Tenant-ID": "550e8400-e29b-41d4-a716-446655440000"}

        ctx_value = None

        async def call_next(request):
            nonlocal ctx_value
            ctx_value = tenant_ctx.get()
            return JSONResponse({"ok": True})

        token = tenant_ctx.set(None)
        try:
            await middleware.dispatch(request, call_next)
            assert ctx_value == "550e8400-e29b-41d4-a716-446655440000"
        finally:
            tenant_ctx.reset(token)

        # After dispatch, context should be reset
        assert tenant_ctx.get() is None

    async def test_skips_when_no_tenant_id(self, middleware):
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/some-endpoint"
        request.headers = {}

        ctx_value = "set"

        async def call_next(request):
            nonlocal ctx_value
            ctx_value = tenant_ctx.get()
            return JSONResponse({"ok": True})

        token = tenant_ctx.set(None)
        try:
            await middleware.dispatch(request, call_next)
            assert ctx_value is None
        finally:
            tenant_ctx.reset(token)

    async def test_skips_excluded_paths(self, middleware):
        request = MagicMock(spec=Request)
        request.url.path = "/docs"
        request.headers = {"X-Tenant-ID": "some-id"}

        ctx_value = None

        async def call_next(request):
            nonlocal ctx_value
            ctx_value = tenant_ctx.get()
            return JSONResponse({"ok": True})

        token = tenant_ctx.set(None)
        try:
            await middleware.dispatch(request, call_next)
            assert ctx_value is None
        finally:
            tenant_ctx.reset(token)

    async def test_excluded_paths_set(self):
        assert "/docs" in TenantContextMiddleware.EXCLUDED_PATHS
        assert "/redoc" in TenantContextMiddleware.EXCLUDED_PATHS
        assert "/openapi.json" in TenantContextMiddleware.EXCLUDED_PATHS
        assert "/api/v1/health" in TenantContextMiddleware.EXCLUDED_PATHS
        assert "/api/v1/ready" in TenantContextMiddleware.EXCLUDED_PATHS
