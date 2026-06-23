import os
import logging

from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor

from ipe_shared.observability.logging import get_correlation_id

logger = logging.getLogger("ipe")


def setup_tracing(
    service_name: str = "unknown",
    version: str = "0.1.0",
    otlp_endpoint: str | None = None,
    console_export: bool = False,
) -> trace.Tracer:
    endpoint = otlp_endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    resource = Resource.create(
        attributes={
            "service.name": service_name,
            "service.version": version,
            "deployment.environment": os.environ.get("IPE_ENV", "development"),
        }
    )

    provider = TracerProvider(resource=resource)

    if endpoint:
        exporter = OTLPSpanExporter(endpoint=endpoint)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        logger.info("OTel tracing enabled, endpoint=%s", endpoint)
    elif console_export:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logger.info("OTel tracing enabled, console exporter")
    else:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logger.info("OTel tracing enabled, console exporter (default)")

    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name, version)


def setup_metrics_export(
    service_name: str = "unknown",
    version: str = "0.1.0",
    otlp_endpoint: str | None = None,
) -> None:
    endpoint = otlp_endpoint or os.environ.get("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", "")
    if not endpoint:
        return

    resource = Resource.create(
        attributes={
            "service.name": service_name,
            "service.version": version,
        }
    )
    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=endpoint),
        export_interval_millis=15000,
    )
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(provider)
    logger.info("OTel metrics export enabled, endpoint=%s", endpoint)


def instrument_app(app, service_name: str = "unknown") -> None:
    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    logger.info("OTel FastAPI instrumented for service=%s", service_name)


def instrument_asyncpg() -> None:
    try:
        AsyncPGInstrumentor().instrument()
        logger.info("OTel asyncpg instrumented")
    except Exception:
        logger.debug("OTel asyncpg instrumentation skipped")


def instrument_redis() -> None:
    try:
        RedisInstrumentor().instrument()
        logger.info("OTel Redis instrumented")
    except Exception:
        logger.debug("OTel Redis instrumentation skipped")