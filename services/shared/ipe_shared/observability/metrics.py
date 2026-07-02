import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from ipe_shared.metrics.middleware import (
    IN_FLIGHT,
    REQUEST_COUNT,
    REQUEST_DURATION,
    MetricsMiddleware,
    setup_prometheus_metrics,
)

logger = logging.getLogger(__name__)

# Backward-compatible alias (label schema changed to include `service`)
ACTIVE_REQUESTS = IN_FLIGHT


async def metrics_endpoint():
    content = generate_latest()
    return Response(content=content, media_type=CONTENT_TYPE_LATEST)


async def health_endpoint():
    return JSONResponse({"status": "ok"})


async def ready_endpoint():
    return JSONResponse({"status": "ready"})


def setup_metrics(app: FastAPI, service_name: str = "unknown") -> None:
    """Wire Prometheus middleware + root health aliases used by some probes."""
    from ipe_shared.config import settings

    version = getattr(settings, "VERSION", "unknown")
    setup_prometheus_metrics(app, service_name=service_name, version=version)

    # Root-level probes (services also expose /api/v1/health via routers)
    app.add_api_route("/health", health_endpoint, methods=["GET"])
    app.add_api_route("/healthz", health_endpoint, methods=["GET"])
    app.add_api_route("/ready", ready_endpoint, methods=["GET"])
