import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from ipe_shared.middleware.cors import setup_cors

from app.api.v1.router import api_router
from app.config import settings
from app.events.consumers import start_consumers, stop_consumers
from app.ws import manager, ws_feasibility_broadcaster
from ipe_shared.auth.jwt import decode_token
from ipe_shared.database.connection import close_database, init_database
from ipe_shared.middleware.error_handler import register_exception_handlers
from ipe_shared.middleware.tenant_context import TenantContextMiddleware
from ipe_shared.metrics import setup_metrics
from ipe_shared.observability import setup_observability

_broadcaster_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _broadcaster_task
    await init_database(settings.DATABASE_URL)
    await start_consumers()
    _broadcaster_task = asyncio.create_task(ws_feasibility_broadcaster())
    yield
    if _broadcaster_task:
        _broadcaster_task.cancel()
    await stop_consumers()
    await close_database()


def create_app() -> FastAPI:
    _app = FastAPI(
        title="IPE - Feasibility Scorer",
        description="Composite gate scoring and auto-confirm logic",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    setup_observability(_app, service_name="fea-svc")
    setup_metrics(_app, service_name="fea-svc", version="9.3.0-p2")

    _app.add_middleware(TenantContextMiddleware)
    setup_cors(_app)
    register_exception_handlers(_app)

    @_app.websocket("/api/v1/feasibility/ws/{tenant_id}")
    async def feasibility_ws(websocket: WebSocket, tenant_id: str):
        token = websocket.query_params.get("token") or websocket.query_params.get("Authorization", "")
        if not token:
            await websocket.close(code=4401)
            return
        try:
            jwt_payload = decode_token(token)
        except Exception:
            await websocket.close(code=4401)
            return

        if str(jwt_payload.tenant_id) != tenant_id:
            await websocket.close(code=4403)
            return

        await manager.connect(tenant_id, websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            await manager.disconnect(tenant_id, websocket)
        except Exception:
            await manager.disconnect(tenant_id, websocket)

    _app.include_router(api_router, prefix="/api/v1")
    return _app


app = create_app()