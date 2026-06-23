import logging
import sys
import uuid
from contextvars import ContextVar

from pythonjsonlogger import jsonlogger

correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


class IPEJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["correlation_id"] = correlation_id.get("") or "unknown"
        log_record["severity"] = record.levelname
        log_record["service_name"] = getattr(record, "service_name", "unknown")
        log_record["version"] = getattr(record, "version", "0.1.0")
        log_record["duration_ms"] = getattr(record, "duration_ms", None)
        if log_record["duration_ms"] is None:
            del log_record["duration_ms"]


def setup_logging(
    level: str = "DEBUG",
    service_name: str = "unknown",
    version: str = "0.1.0",
) -> logging.Logger:
    logger = logging.getLogger("ipe")
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = IPEJsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)

    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service_name = service_name
        record.version = version
        return record

    logging.setLogRecordFactory(record_factory)

    return logger


def get_correlation_id() -> str:
    return correlation_id.get("")


def set_correlation_id(cid: str | None = None) -> str:
    cid = cid or str(uuid.uuid4())
    correlation_id.set(cid)
    return cid