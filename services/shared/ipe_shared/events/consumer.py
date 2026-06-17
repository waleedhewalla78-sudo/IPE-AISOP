import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime

from aiokafka import AIOKafkaConsumer

from ipe_shared.cache.redis_client import redis_client
from ipe_shared.config import settings
from ipe_shared.events.producer import kafka_producer

logger = logging.getLogger(__name__)


class KafkaConsumer:
    def __init__(
        self, topics: list[str], group_id: str, handler: Callable, service_name: str = "unknown"
    ):
        self.service_name = service_name
        self.consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            value_deserializer=lambda v: json.loads(v.decode()),
        )
        self.handler = handler

    async def start(self):
        await self.consumer.start()
        try:
            await redis_client.start()
        except Exception as e:
            logger.warning("Redis not available, idempotency disabled: %s", e)
        async for msg in self.consumer:
            try:
                value = msg.value if hasattr(msg, "value") else msg
                if isinstance(value, dict):
                    event_id = value.get("event_id") or value.get("data", {}).get("event_id", "")
                    if event_id:
                        dedup_key = f"ipe:processed:{self.service_name}:{event_id}"
                        already_processed = await redis_client.check_and_set_dedup(dedup_key)
                        if already_processed:
                            logger.warning(
                                "Skipping duplicate event %s for service %s",
                                event_id,
                                self.service_name,
                            )
                            continue

                await self.handler(msg)

            except Exception as e:
                logger.error(
                    "Handler failed for service %s, event: %s. Error: %s",
                    self.service_name,
                    msg.value if hasattr(msg, "value") else msg,
                    e,
                    exc_info=True,
                )
                try:
                    dlq_topic = f"ipe.dlq.{self.service_name}"
                    failed_payload = {
                        "original_message": msg.value if hasattr(msg, "value") else msg,
                        "error_message": str(e),
                        "failed_at": datetime.now(UTC).isoformat(),
                        "topic": msg.topic if hasattr(msg, "topic") else "",
                    }
                    if isinstance(failed_payload["original_message"], dict):
                        failed_payload["original_message"].pop("error_message", None)
                    await kafka_producer.send(dlq_topic, key="dlq", value=failed_payload)
                    logger.info("Sent failed event to DLQ: %s", dlq_topic)
                except Exception as dlq_e:
                    logger.error("Failed to send to DLQ: %s", dlq_e)

    async def stop(self):
        await self.consumer.stop()
