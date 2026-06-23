from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.events.consumers import start_consumers, stop_consumers
from ipe_shared.database.connection import close_database, init_database
from ipe_shared.middleware.error_handler import register_exception_handlers
from ipe_shared.middleware.tenant_context import TenantContextMiddleware
from ipe_shared.observability import setup_observability

def create_app() -> FastAPI:
    _app = FastAPI(
        title="IPE - Demand & Priority Engine",
        description="Demand classification and priority scoring service",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    setup_observability(_app, service_name="dpe-svc")

    _app.add_middleware(TenantContextMiddleware)
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Tenant-ID"],
    )

    register_exception_handlers(_app)

    _app.include_router(api_router, prefix="/api/v1")

    @_app.on_event("startup")
    async def startup():
        await init_database(settings.DATABASE_URL)
        await start_consumers()

    @_app.on_event("shutdown")
    async def shutdown():
        await stop_consumers()
        await close_database()

    return _app


app = create_app()