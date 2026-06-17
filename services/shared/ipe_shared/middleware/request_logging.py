import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("ipe.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        elapsed_ms = (time.monotonic() - start) * 1000

        logger.info(
            "request_id=%s method=%s path=%s status=%d elapsed_ms=%.1f",
            getattr(request.state, "correlation_id", "-"),
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
