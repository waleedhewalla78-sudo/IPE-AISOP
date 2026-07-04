import logging
import os

from ipe_shared.config import settings
from ipe_shared.observability.logging import setup_logging, set_correlation_id
from ipe_shared.observability.tracing import (
    setup_tracing,
    setup_metrics_export,
    instrument_app,
    instrument_asyncpg,
    instrument_redis,
)
from ipe_shared.observability.metrics import setup_health_probes
from ipe_shared.observability.middleware import (
    CorrelationIdMiddleware,
    RequestLoggingMiddleware,
)
from ipe_shared.middleware.audit_request import AuditRequestMiddleware

logger = logging.getLogger("ipe")


def setup_observability(app, service_name: str | None = None) -> None:
    name = service_name or settings.SERVICE_NAME
    version = settings.VERSION

    if settings.OTEL_LOGGING_ENABLED:
        setup_logging(
            level=settings.LOG_LEVEL,
            service_name=name,
            version=version,
        )
        logger.info("Structured JSON logging enabled for service=%s", name)
    else:
        logging.basicConfig(level=settings.LOG_LEVEL)
        logger.info("Standard logging enabled for service=%s", name)

    if settings.OTEL_TRACING_ENABLED:
        tracer = setup_tracing(
            service_name=name,
            version=version,
            otlp_endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT or None,
        )
        setup_metrics_export(
            service_name=name,
            version=version,
            otlp_endpoint=settings.OTEL_EXPORTER_OTLP_METRICS_ENDPOINT or None,
        )
        instrument_app(app, service_name=name)
        logger.info("OTel tracing instrumented for service=%s", name)

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    if settings.AUDIT_REQUEST_MIDDLEWARE:
        app.add_middleware(AuditRequestMiddleware)
        logger.info("Audit request middleware enabled for service=%s", name)

    setup_health_probes(app)

    try:
        instrument_asyncpg()
    except Exception as e:
        logger.warning("AsyncPG instrumentation failed: %s", e)

    try:
        instrument_redis()
    except Exception as e:
        logger.warning("Redis instrumentation failed: %s", e)

    logger.info("Observability setup complete for service=%s version=%s", name, version)