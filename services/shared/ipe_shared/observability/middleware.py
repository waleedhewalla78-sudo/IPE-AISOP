import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ipe_shared.observability.logging import set_correlation_id, get_correlation_id


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        set_correlation_id(cid)
        request.state.correlation_id = cid

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000

        response.headers["X-Correlation-ID"] = cid
        response.headers["X-Request-Duration-Ms"] = f"{duration_ms:.2f}"
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        import logging
        _logger = logging.getLogger("ipe.request")

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000

        _logger.info(
            "request_id=%s method=%s path=%s status=%s elapsed_ms=%.1f",
            get_correlation_id(),
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={"duration_ms": round(duration_ms, 2)},
        )
        return response