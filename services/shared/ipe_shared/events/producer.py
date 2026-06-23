import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from aiokafka import AIOKafkaProducer
from fastavro import parse_schema, writer as avro_writer
from io import BytesIO

from ipe_shared.config import settings

logger = logging.getLogger(__name__)


class KafkaProducer:
    def __init__(self):
        self._producer: AIOKafkaProducer | None = None
        self._avro_schemas: dict[str, tuple[dict, Any]] = {}

    def _load_avro_schema(self, schema_name: str) -> tuple[dict, Any] | None:
        if schema_name in self._avro_schemas:
            return self._avro_schemas[schema_name]
        try:
            import json as _json
            from pathlib import Path

            schema_path = Path(__file__).parent / "schemas" / f"{schema_name}.avsc"
            if schema_path.exists():
                with open(schema_path) as f:
                    schema_json = _json.load(f)
                parsed = parse_schema(schema_json)
                self._avro_schemas[schema_name] = (schema_json, parsed)
                return self._avro_schemas[schema_name]
        except Exception as e:
            logger.debug("Could not load Avro schema '%s': %s", schema_name, e)
        return None

    async def start(self):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: v if isinstance(v, bytes) else json.dumps(v).encode(),
        )
        await self._producer.start()

    async def stop(self):
        if self._producer:
            await self._producer.stop()
            self._producer = None

    async def send(self, topic: str, key: str, value: dict):
        if self._producer is None:
            await self.start()
        await self._producer.send(topic, key=key.encode(), value=value)

    async def send_event(self, entity: str, event: str, key: str, value: dict):
        topic = f"ipe.{entity}.{event}"
        await self.send(topic, key, value)

    async def send_avro(self, topic: str, key: str, envelope: dict):
        if self._producer is None:
            await self.start()
        schema_name = topic.replace(".", "_")
        schema_info = self._load_avro_schema(schema_name)
        if schema_info:
            _, parsed = schema_info
            buf = BytesIO()
            avro_writer(buf, parsed, [envelope])
            payload = buf.getvalue()
        else:
            payload = json.dumps(envelope).encode()
        await self._producer.send(topic, key=key.encode(), value=payload)

    def build_envelope(self, event_type: str, tenant_id: str, payload: dict) -> dict:
        return {
            "event_id": str(uuid4()),
            "tenant_id": str(tenant_id),
            "event_type": event_type,
            "occurred_at": datetime.now(UTC).isoformat(),
            "schema_version": 1,
            "payload": payload,
        }


kafka_producer = KafkaProducer()
