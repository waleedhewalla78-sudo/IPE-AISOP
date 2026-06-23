import logging
import time

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Gauge, Histogram, CONTENT_TYPE_LATEST, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

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

EXCLUDED_METRICS_PATHS = {"/metrics", "/health", "/ready"}


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXCLUDED_METRICS_PATHS:
            return await call_next(request)

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


async def metrics_endpoint():
    content = generate_latest()
    return Response(content=content, media_type=CONTENT_TYPE_LATEST)


async def health_endpoint():
    return JSONResponse({"status": "ok"})


async def ready_endpoint():
    return JSONResponse({"status": "ready"})


def setup_metrics(app: FastAPI, service_name: str = "unknown"):
    app.add_middleware(MetricsMiddleware)
    app.add_api_route("/metrics", metrics_endpoint, methods=["GET"])
    app.add_api_route("/health", health_endpoint, methods=["GET"])
    app.add_api_route("/ready", ready_endpoint, methods=["GET"])

    try:
        info = Gauge("ipe_service_info", "Service metadata", ["service", "version"])
        info.labels(service=service_name, version="0.1.0").set(1)
    except ValueError as e:
        logger.debug("Service info gauge already registered: %s", e)
