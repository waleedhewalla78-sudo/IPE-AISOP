import time

from fastapi import FastAPI
from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

REQUEST_COUNT = Counter(
    "ipe_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_DURATION = Histogram(
    "ipe_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)
ACTIVE_REQUESTS = Gauge(
    "ipe_http_requests_active",
    "Number of active HTTP requests",
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ACTIVE_REQUESTS.inc()
        start = time.monotonic()
        response = await call_next(request)
        duration = time.monotonic() - start
        ACTIVE_REQUESTS.dec()

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).inc()
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)

        return response


def setup_metrics(app: FastAPI, service_name: str = "unknown"):
    app.add_middleware(MetricsMiddleware)

    try:
        info = Gauge("ipe_service_info", "Service metadata", ["service", "version"])
        info.labels(service=service_name, version="0.1.0").set(1)
    except ValueError:
        pass
