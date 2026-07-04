from contextlib import asynccontextmanager

from fastapi import FastAPI
from ipe_shared.middleware.cors import setup_cors

from app.api.v1.router import router as api_router
from app.config import settings
from ipe_shared.middleware.error_handler import register_exception_handlers
from ipe_shared.middleware.tenant_context import TenantContextMiddleware
from ipe_shared.metrics import setup_metrics
from ipe_shared.observability import setup_observability


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    _app = FastAPI(
        title="IPE - Sustainability Service",
        description="Circularity scoring, EOL planning, recyclability scoring, and carbon tracking",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    setup_observability(_app, service_name="sustain-svc")
    setup_metrics(_app, service_name="sustain-svc", version="9.3.0-p2")
    _app.add_middleware(TenantContextMiddleware)
    _    setup_cors(app)
    register_exception_handlers(_app)
    _app.include_router(api_router, prefix="/api/v1")
    return _app


app = create_app()