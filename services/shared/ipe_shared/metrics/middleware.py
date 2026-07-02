"""Prometheus metrics middleware for FastAPI services.

Tracks request duration, error rate, in-flight requests, DB pool stats,
and Kafka consumer lag.
"""

from __future__ import annotations

import logging
import re
import time

from fastapi import FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, Info, REGISTRY, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

REQUEST_COUNT = Counter(
    "ipe_http_requests_total",
    "Total HTTP requests",
    ["service", "method", "endpoint", "status_code"],
)

REQUEST_DURATION = Histogram(
    "ipe_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["service", "method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

IN_FLIGHT = Gauge(
    "ipe_http_requests_in_flight",
    "Current in-flight requests",
    ["service"],
)

DB_POOL_SIZE = Gauge(
    "ipe_db_pool_size",
    "Database connection pool size",
    ["service"],
)

DB_POOL_CHECKED_OUT = Gauge(
    "ipe_db_pool_checked_out",
    "Database connections currently checked out",
    ["service"],
)

DB_POOL_OVERFLOW = Gauge(
    "ipe_db_pool_overflow",
    "Database overflow connections",
    ["service"],
)

KAFKA_CONSUMER_LAG = Gauge(
    "ipe_kafka_consumer_lag",
    "Kafka consumer group lag",
    ["service", "topic", "consumer_group"],
)

SERVICE_INFO = Info(
    "ipe_service_info",
    "Service metadata",
)

EXCLUDED_METRICS_PATHS = {"/metrics", "/health", "/healthz", "/ready"}

_UUID_PATTERN = re.compile(
    r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)
_NUMERIC_ID_PATTERN = re.compile(r"/\d+(?=/|$)")


class MetricsMiddleware(BaseHTTPMiddleware):
    """Tracks HTTP metrics for every request."""

    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in EXCLUDED_METRICS_PATHS:
            return await call_next(request)

        method = request.method
        endpoint = self._normalize_path(request.url.path)

        IN_FLIGHT.labels(service=self.service_name).inc()
        start = time.perf_counter()

        try:
            response = await call_next(request)
            REQUEST_COUNT.labels(
                service=self.service_name,
                method=method,
                endpoint=endpoint,
                status_code=str(response.status_code),
            ).inc()
            return response
        except Exception:
            REQUEST_COUNT.labels(
                service=self.service_name,
                method=method,
                endpoint=endpoint,
                status_code="500",
            ).inc()
            raise
        finally:
            duration = time.perf_counter() - start
            REQUEST_DURATION.labels(
                service=self.service_name,
                method=method,
                endpoint=endpoint,
            ).observe(duration)
            IN_FLIGHT.labels(service=self.service_name).dec()

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Replace UUIDs and numeric IDs with placeholders."""
        path = _UUID_PATTERN.sub("/{id}", path)
        return _NUMERIC_ID_PATTERN.sub("/{id}", path)


def _collect_db_pool_metrics(service_name: str) -> None:
    try:
        from ipe_shared.database.connection import get_engine

        pool = get_engine().sync_engine.pool
        DB_POOL_SIZE.labels(service=service_name).set(pool.size())
        DB_POOL_CHECKED_OUT.labels(service=service_name).set(pool.checkedout())
        DB_POOL_OVERFLOW.labels(service=service_name).set(pool.overflow())
    except (RuntimeError, ImportError, AttributeError):
        pass


def record_kafka_consumer_lag(service: str, topic: str, consumer_group: str, lag: int) -> None:
    """Update Kafka consumer lag gauge (call from consumer loops)."""
    KAFKA_CONSUMER_LAG.labels(
        service=service,
        topic=topic,
        consumer_group=consumer_group,
    ).set(lag)


def setup_prometheus_metrics(app: FastAPI, service_name: str, version: str = "unknown") -> None:
    """Attach metrics middleware and /metrics endpoint to a FastAPI app."""
    app.add_middleware(MetricsMiddleware, service_name=service_name)

    try:
        SERVICE_INFO.info({"service": service_name, "version": version})
    except Exception as exc:
        logger.debug("Service info metric already set: %s", exc)

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        _collect_db_pool_metrics(service_name)
        return Response(
            content=generate_latest(REGISTRY),
            media_type=CONTENT_TYPE_LATEST,
        )
