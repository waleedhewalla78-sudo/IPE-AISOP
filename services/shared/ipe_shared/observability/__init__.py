from ipe_shared.metrics.middleware import IN_FLIGHT, REQUEST_COUNT, REQUEST_DURATION
from ipe_shared.observability.logging import (
    setup_logging,
    get_correlation_id,
    set_correlation_id,
    correlation_id,
)
from ipe_shared.observability.metrics import setup_metrics
from ipe_shared.observability.tracing import (
    setup_tracing,
    setup_metrics_export,
    instrument_app,
    instrument_asyncpg,
    instrument_redis,
)
from ipe_shared.observability.middleware import (
    CorrelationIdMiddleware,
    RequestLoggingMiddleware,
)
from ipe_shared.observability.setup import setup_observability

ACTIVE_REQUESTS = IN_FLIGHT

__all__ = [
    "setup_logging",
    "get_correlation_id",
    "set_correlation_id",
    "correlation_id",
    "setup_metrics",
    "REQUEST_COUNT",
    "REQUEST_DURATION",
    "ACTIVE_REQUESTS",
    "setup_tracing",
    "setup_metrics_export",
    "instrument_app",
    "instrument_asyncpg",
    "instrument_redis",
    "CorrelationIdMiddleware",
    "RequestLoggingMiddleware",
    "setup_observability",
]