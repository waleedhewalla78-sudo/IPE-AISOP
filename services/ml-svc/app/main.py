from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from ipe_shared.database.connection import close_database, init_database
from ipe_shared.middleware.correlation_id import CorrelationIdMiddleware
from ipe_shared.middleware.error_handler import register_exception_handlers
from ipe_shared.middleware.request_logging import RequestLoggingMiddleware
from ipe_shared.middleware.tenant_context import TenantContextMiddleware
from ipe_shared.observability.setup import setup_observability


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.DATABASE_URL:
        await init_database(settings.DATABASE_URL)
    yield
    if settings.DATABASE_URL:
        await close_database()


def create_app() -> FastAPI:
    app = FastAPI(
        title="IPE - ML Duration Predictor",
        description="XGBoost/Random Forest duration prediction with MLflow",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(TenantContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Tenant-ID"],
    )
    register_exception_handlers(app)
    setup_observability(app, service_name="ml-svc")
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
