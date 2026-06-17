import pytest
from unittest.mock import AsyncMock, MagicMock

from starlette.requests import Request
from starlette.responses import JSONResponse

from ipe_shared.middleware.correlation_id import CorrelationIdMiddleware
from ipe_shared.middleware.error_handler import register_exception_handlers
from ipe_shared.middleware.request_logging import RequestLoggingMiddleware


class TestCorrelationIdMiddleware:
    @pytest.fixture
    def middleware(self):
        app = AsyncMock()
        return CorrelationIdMiddleware(app)

    async def test_sets_correlation_id(self, middleware):
        request = MagicMock(spec=Request)
        request.headers = {"X-Correlation-ID": "test-corr-id"}
        request.url.path = "/test"

        resp = MagicMock()
        resp.headers = {}
        call_next = AsyncMock(return_value=resp)

        response = await middleware.dispatch(request, call_next)
        assert response.headers.get("X-Correlation-ID") == "test-corr-id"


class TestRequestLoggingMiddleware:
    @pytest.fixture
    def middleware(self):
        app = AsyncMock()
        return RequestLoggingMiddleware(app)

    async def test_passes_request_through(self, middleware):
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url.path = "/test"
        request.headers = {}
        request.state.correlation_id = "corr-123"

        call_next = AsyncMock(return_value=JSONResponse({"ok": True}))

        response = await middleware.dispatch(request, call_next)
        assert response is not None


class TestErrorHandler:
    def test_register_exception_handlers(self):
        app = MagicMock()
        register_exception_handlers(app)
        assert app.exception_handler.call_count == 2


