import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def metrics_endpoint():
    """Legacy import path — prefer ipe_shared.metrics.setup_metrics /metrics route."""
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    from starlette.responses import Response

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def health_endpoint():
    return JSONResponse({"status": "ok"})


async def ready_endpoint():
    return JSONResponse({"status": "ready"})


def setup_health_probes(app: FastAPI) -> None:
    """Root-level probes used by Kong and container healthchecks."""
    app.add_api_route("/health", health_endpoint, methods=["GET"])
    app.add_api_route("/healthz", health_endpoint, methods=["GET"])
    app.add_api_route("/ready", ready_endpoint, methods=["GET"])


def setup_metrics(app: FastAPI, service_name: str = "unknown") -> None:
    """Backward-compatible helper: Prometheus metrics + health probes."""
    from ipe_shared.config import settings
    from ipe_shared.metrics import setup_metrics as setup_prometheus_metrics

    version = getattr(settings, "VERSION", "unknown")
    setup_prometheus_metrics(app, service_name=service_name, version=version)
    setup_health_probes(app)
