from contextlib import asynccontextmanager
from fastapi import FastAPI
from ipe_shared.middleware.cors import setup_cors

from ipe_shared.middleware.tenant_context import TenantContextMiddleware
from ipe_shared.middleware.request_logging import RequestLoggingMiddleware
from ipe_shared.middleware.error_handler import register_exception_handlers
from ipe_shared.middleware.correlation_id import CorrelationIdMiddleware
from ipe_shared.metrics import setup_metrics
from ipe_shared.observability.setup import setup_observability
from ipe_shared.database.connection import init_database, close_database

from app.config import settings
from app.api.v1.router import api_router
from app.events.consumers import start_consumers, stop_consumers
from app.jobs.sync_scheduler import start_sync_scheduler, stop_sync_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_database(settings.DATABASE_URL)
    await start_consumers()
    start_sync_scheduler()
    yield
    await stop_sync_scheduler()
    await stop_consumers()
    await close_database()


def create_app() -> FastAPI:
    app = FastAPI(
        title="IPE - Odoo Connector",
        description="ERP synchronization adapter for Odoo",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(TenantContextMiddleware)
    setup_cors(app)
    register_exception_handlers(app)
    setup_observability(app, service_name="connector")
    setup_metrics(app, service_name="connector", version="9.3.0-p2")
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
