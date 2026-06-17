import json

from aiokafka import AIOKafkaProducer

from ipe_shared.config import settings


class KafkaProducer:
    def __init__(self):
        self._producer: AIOKafkaProducer | None = None

    async def start(self):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode(),
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


kafka_producer = KafkaProducer()
