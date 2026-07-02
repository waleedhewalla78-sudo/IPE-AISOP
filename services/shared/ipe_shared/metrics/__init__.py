"""Prometheus metrics for IPE services."""

from ipe_shared.metrics.middleware import (
    DB_POOL_CHECKED_OUT,
    DB_POOL_OVERFLOW,
    DB_POOL_SIZE,
    IN_FLIGHT,
    KAFKA_CONSUMER_LAG,
    REQUEST_COUNT,
    REQUEST_DURATION,
    MetricsMiddleware,
    record_kafka_consumer_lag,
    setup_prometheus_metrics,
)

__all__ = [
    "DB_POOL_CHECKED_OUT",
    "DB_POOL_OVERFLOW",
    "DB_POOL_SIZE",
    "IN_FLIGHT",
    "KAFKA_CONSUMER_LAG",
    "REQUEST_COUNT",
    "REQUEST_DURATION",
    "MetricsMiddleware",
    "record_kafka_consumer_lag",
    "setup_prometheus_metrics",
]
