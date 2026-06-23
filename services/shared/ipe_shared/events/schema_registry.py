import logging
from pathlib import Path
from typing import Any

import httpx

from ipe_shared.config import settings

logger = logging.getLogger(__name__)

SCHEMA_DIR = Path(__file__).parent / "schemas"

_avro_schemas: dict[str, dict] | None = None


def _load_schemas() -> dict[str, dict]:
    global _avro_schemas
    if _avro_schemas is not None:
        return _avro_schemas
    _avro_schemas = {}
    if SCHEMA_DIR.is_dir():
        for f in sorted(SCHEMA_DIR.glob("*.avsc")):
            import json

            with open(f) as fh:
                _avro_schemas[f.stem] = json.load(fh)
    return _avro_schemas


def get_avro_schema(topic: str) -> dict[str, Any] | None:
    schemas = _load_schemas()
    name = topic.replace(".", "_")
    return schemas.get(name)


async def register_schema(subject: str, schema_json: dict) -> bool:
    url = f"{settings.SCHEMA_REGISTRY_URL}/subjects/{subject}/versions"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json={"schema": schema_json})
            if resp.status_code in (200, 201):
                logger.info(
                    "Registered schema for subject %s (id=%s)", subject, resp.json().get("id")
                )
                return True
            if resp.status_code == 409:
                logger.info("Schema for subject %s already exists", subject)
                return True
            logger.warning(
                "Failed to register schema for %s: %s %s", subject, resp.status_code, resp.text
            )
            return False
    except Exception as e:
        logger.warning("Cannot connect to Schema Registry: %s", e)
        return False


def get_latest_schema(subject: str) -> dict | None:
    schemas = _load_schemas()
    topic_key = subject.replace("-value", "").replace(".", "_")
    return schemas.get(topic_key)
