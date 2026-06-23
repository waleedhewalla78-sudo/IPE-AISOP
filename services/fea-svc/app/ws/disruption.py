import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


class DisruptionBroadcaster:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, event: dict[str, Any]):
        data = json.dumps(event)
        disconnected = []
        for ws in self.connections:
            try:
                await ws.send_text(data)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)


broadcaster = DisruptionBroadcaster()


@router.websocket("/ws/disruption/{tenant_id}")
async def disruption_ws(ws: WebSocket, tenant_id: str):
    await broadcaster.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            try:
                event = json.loads(data)
                if event.get("type") == "ping":
                    await ws.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                logger.warning("Disruption WS: received non-JSON message, ignoring")
    except WebSocketDisconnect:
        broadcaster.disconnect(ws)


async def publish_disruption(event: dict[str, Any]):
    await broadcaster.broadcast(event)
