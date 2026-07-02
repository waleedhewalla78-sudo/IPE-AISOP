from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from ipe_shared.database.connection import close_database, init_database
from ipe_shared.middleware.error_handler import register_exception_handlers
from ipe_shared.middleware.tenant_context import TenantContextMiddleware
from ipe_shared.observability import setup_observability


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_database(settings.DATABASE_URL)
    yield
    await close_database()


def create_app() -> FastAPI:
    app = FastAPI(title="IPE - Scenario Workbench", version=settings.VERSION, lifespan=lifespan)
    setup_observability(app, service_name=settings.SERVICE_NAME)
    app.add_middleware(TenantContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Tenant-ID"],
    )
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
