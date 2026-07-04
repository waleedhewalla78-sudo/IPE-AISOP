import json
import logging
from collections import defaultdict
from io import BytesIO

from aiokafka import AIOKafkaConsumer
from fastapi import WebSocket

from ipe_shared.config import settings
from ipe_shared.events.consumer import get_consumer_group, resolve_consumer_tenant_id

logger = logging.getLogger(__name__)

_AVRO_TOPIC = "ipe.mo.feasibility_scored"


def _try_avro_decode(data: bytes) -> dict | None:
    try:
        from fastavro import reader as avro_reader
        buf = BytesIO(data)
        for record in avro_reader(buf):
            return record
    except Exception:
        return None


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, tenant_id: str, ws: WebSocket):
        await ws.accept()
        self._connections[tenant_id].append(ws)

    async def disconnect(self, tenant_id: str, ws: WebSocket):
        self._connections[tenant_id].remove(ws)
        if not self._connections[tenant_id]:
            del self._connections[tenant_id]

    async def broadcast(self, tenant_id: str, message: dict):
        dead = []
        for ws in self._connections.get(tenant_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections[tenant_id].remove(ws)


manager = ConnectionManager()


async def ws_feasibility_broadcaster():
    base_group = "fea-svc-ws"
    tenant_id = resolve_consumer_tenant_id()
    group_id = get_consumer_group(base_group, tenant_id) if tenant_id else base_group
    consumer = AIOKafkaConsumer(
        _AVRO_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=group_id,
        value_deserializer=lambda v: v,
    )
    await consumer.start()
    try:
        async for msg in consumer:
            raw = msg.value if hasattr(msg, "value") else msg
            if not raw:
                continue
            value = _try_avro_decode(raw)
            if value is None:
                try:
                    value = json.loads(raw.decode())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    logger.warning("Cannot decode message on %s, skipping", _AVRO_TOPIC)
                    continue
            tenant_id = value.get("tenant_id")
            if tenant_id:
                await manager.broadcast(str(tenant_id), value)
    except Exception:
        logger.exception("WebSocket broadcaster failed")
    finally:
        await consumer.stop()
