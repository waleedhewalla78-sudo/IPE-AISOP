from contextlib import asynccontextmanager

from fastapi import FastAPI
from ipe_shared.middleware.cors import setup_cors

from app.api.v1.router import api_router
from app.config import settings
from app.events.consumers import start_consumers, stop_consumers
from app.middleware.pii import PIIStrippingMiddleware
from ipe_shared.database.connection import close_database, init_database
from ipe_shared.middleware.error_handler import register_exception_handlers
from ipe_shared.middleware.tenant_context import TenantContextMiddleware
from ipe_shared.metrics import setup_metrics
from ipe_shared.observability import setup_observability


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging

    logger = logging.getLogger("nlp-svc")
    await init_database(settings.DATABASE_URL)
    await start_consumers()
    # Fix 1A: warm LLM connection so first user request is not cold-start
    try:
        from app.core.llm_client import get_tool_agent_backend

        backend = get_tool_agent_backend()
        if backend is not None:
            logger.info("LLM warm-up: backend=%s ready", backend.provider)
        else:
            logger.warning("LLM warm-up skipped — no LLM backend configured")
    except Exception as exc:
        logger.warning("LLM warm-up failed (non-fatal): %s", exc)
    yield
    await stop_consumers()
    await close_database()


def create_app() -> FastAPI:
    _app = FastAPI(
        title="IPE - Copilot Interface",
        description=(
            "Natural language query processing"
            " and LLM orchestration"
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    setup_observability(_app, service_name="nlp-svc")
    setup_metrics(_app, service_name="nlp-svc", version="9.3.0-p2")
    _app.add_middleware(PIIStrippingMiddleware)
    _app.add_middleware(TenantContextMiddleware)
    setup_cors(_app)
    register_exception_handlers(_app)
    _app.include_router(api_router, prefix="/api/v1")
    return _app


app = create_app()
