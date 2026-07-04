import json
import logging
import os
import re
import traceback
from collections.abc import Callable
from datetime import UTC, datetime
from io import BytesIO
from typing import Any

from aiokafka import AIOKafkaConsumer

from ipe_shared.cache.redis_client import redis_client
from ipe_shared.config import settings
from ipe_shared.events.producer import kafka_producer
from ipe_shared.metrics.middleware import KAFKA_CONSUMER_LAG
from ipe_shared.middleware.tenant_context import tenant_ctx

logger = logging.getLogger(__name__)


def _sanitize_group_component(value: str) -> str:
    """Kafka group IDs allow alphanumerics, dots, hyphens, and underscores."""
    return re.sub(r"[^a-zA-Z0-9._-]", "-", value.strip())


def get_consumer_group(base_name: str, tenant_id: str) -> str:
    """Return tenant-scoped consumer group name."""
    return f"ipe.{_sanitize_group_component(tenant_id)}.{_sanitize_group_component(base_name)}"


def resolve_consumer_tenant_id(explicit: str | None = None) -> str | None:
    """Resolve tenant ID for Kafka consumer group scoping."""
    if explicit and str(explicit).strip():
        return str(explicit).strip()
    configured = getattr(settings, "KAFKA_CONSUMER_TENANT_ID", "") or ""
    if configured.strip():
        return configured.strip()
    for key in ("IPE_KAFKA_CONSUMER_TENANT_ID", "IPE_TENANT_ID", "TENANT_ID"):
        val = os.getenv(key, "").strip()
        if val:
            return val
    return None


def _try_avro_deserialize(data: bytes) -> dict | None:
    try:
        from fastavro import reader as avro_reader

        buf = BytesIO(data)
        for record in avro_reader(buf):
            return record
    except Exception:
        return None


async def publish_dlq(service_name: str, original: Any, error: str):
    dlq_topic = f"ipe.dlq.{service_name}"
    failed_payload = {
        "original_message": original,
        "error_message": error,
        "failed_at": datetime.now(UTC).isoformat(),
    }
    try:
        await kafka_producer.send(dlq_topic, key="dlq", value=failed_payload)
    except Exception as e:
        logger.error("Failed to send to DLQ: %s", e)


def _get_envelope(value: dict) -> tuple[dict, str]:
    """Extract envelope fields and return (payload_dict, tenant_id)."""
    envelope_tenant = value.get("tenant_id") or value.get("data", {}).get("tenant_id", "")
    payload = value.get("payload", value)
    return payload, str(envelope_tenant) if envelope_tenant else ""


class KafkaConsumer:
    def __init__(
        self,
        topics: list[str],
        group_id: str,
        handler: Callable,
        service_name: str = "unknown",
        use_session: bool = False,
        tenant_id: str | None = None,
        tenant_scoped: bool = True,
    ):
        self.service_name = service_name
        self.base_group_id = group_id
        self.consumer_tenant_id = resolve_consumer_tenant_id(tenant_id)
        if tenant_scoped and self.consumer_tenant_id:
            self.group_id = get_consumer_group(group_id, self.consumer_tenant_id)
        else:
            self.group_id = group_id
            if tenant_scoped and not self.consumer_tenant_id:
                logger.warning(
                    "Kafka consumer %s using shared group %s — set IPE_KAFKA_CONSUMER_TENANT_ID",
                    service_name,
                    group_id,
                )
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        self.handler = handler
        self._avro_topics = set()
        self._use_session = use_session

        try:
            from pathlib import Path

            schema_dir = Path(__file__).parent / "schemas"
            if schema_dir.is_dir():
                for f in schema_dir.glob("*.avsc"):
                    topic_name = f.stem.replace("_", ".")
                    self._avro_topics.add(topic_name)
        except Exception:
            logger.warning("Could not load Avro schemas for consumer topics", exc_info=True)

        self.consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda v: v,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
        )

    async def start(self):
        await self.consumer.start()
        try:
            await redis_client.start()
        except Exception as e:
            logger.warning("Redis not available, idempotency disabled: %s", e)
        async for msg in self.consumer:
            await self._process_message(msg)

    async def _report_consumer_lag(self, topic: str, consumer_group: str | None = None) -> None:
        """Report current consumer lag to Prometheus."""
        group = consumer_group or self.group_id
        try:
            assigned = self.consumer.assignment()
            partitions = [tp for tp in assigned if tp.topic == topic]
            if not partitions:
                return

            end_offsets = await self.consumer.end_offsets(partitions)
            max_lag = 0
            for tp in partitions:
                committed = await self.consumer.committed(tp)
                current = committed if committed is not None else await self.consumer.position(tp)
                lag = end_offsets.get(tp, 0) - current
                max_lag = max(max_lag, max(0, lag))

            KAFKA_CONSUMER_LAG.labels(
                service=self.service_name,
                topic=topic,
                consumer_group=group,
            ).set(max_lag)
        except Exception:
            pass  # Non-critical — don't break consumer loop

    async def _process_message(self, msg: Any):
        raw_value = msg.value if hasattr(msg, "value") else msg
        topic = msg.topic if hasattr(msg, "topic") else ""
        await self._report_consumer_lag(topic)

        if isinstance(raw_value, bytes) and topic in self._avro_topics:
            deserialized = _try_avro_deserialize(raw_value)
            if deserialized:
                value = deserialized
            else:
                try:
                    value = json.loads(raw_value.decode())
                except Exception:
                    value = raw_value
        elif isinstance(raw_value, bytes):
            try:
                value = json.loads(raw_value.decode())
            except Exception:
                value = raw_value
        else:
            value = raw_value

        if not isinstance(value, dict):
            logger.warning("Non-dict message on %s, skipping", topic)
            await self.consumer.commit()
            return

        event_id = value.get("event_id", "")
        payload, envelope_tenant_id = _get_envelope(value)

        # Crash-safe idempotency: check key BEFORE processing
        if event_id:
            dedup_key = f"ipe:processed:{self.service_name}:{event_id}"
            try:
                already = await redis_client.check_key(dedup_key)
                if already:
                    logger.warning(
                        "Skipping duplicate event %s for service %s", event_id, self.service_name
                    )
                    await self.consumer.commit()
                    return
            except Exception as e:
                logger.warning("Idempotency check failed for event %s: %s", event_id, e)

        # Set tenant context from envelope
        if envelope_tenant_id:
            token = tenant_ctx.set(envelope_tenant_id)
        else:
            token = None

        try:
            # Process with or without session helper
            if self._use_session:
                from ipe_shared.database.session import get_session

                async with get_session() as session:
                    async with session.begin():
                        await self.handler(session, payload)
            else:
                await self.handler(payload)

            # CRASH-SAFE: set Redis key ONLY after successful processing
            if event_id:
                try:
                    await redis_client.set_key(dedup_key, "1", ttl=86400)
                except Exception as e:
                    logger.warning("Redis idempotency key failed for event %s: %s", event_id, e)

            await self.consumer.commit()

        except Exception as e:
            logger.error(
                "Handler failed for service %s, topic: %s, event: %s. Error: %s",
                self.service_name,
                topic,
                event_id,
                e,
                exc_info=True,
            )
            try:
                dlq_value = raw_value.decode() if isinstance(raw_value, bytes) else value
                await publish_dlq(self.service_name, dlq_value, traceback.format_exc())
            except Exception as e:
                logger.error("DLQ publish failed for %s: %s", self.service_name, e)
            # Commit offset so bad messages aren't infinitely redelivered
            await self.consumer.commit()

        finally:
            if token:
                tenant_ctx.reset(token)

    async def stop(self):
        await self.consumer.stop()
