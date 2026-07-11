from contextlib import asynccontextmanager

from fastapi import FastAPI
from ipe_shared.middleware.cors import setup_cors

from app.api.v1.router import api_router
from app.config import settings
from app.consumers.supply_feedback_consumer import start_consumers, stop_consumers
from ipe_shared.database.connection import close_database, init_database
from ipe_shared.middleware.error_handler import register_exception_handlers
from ipe_shared.middleware.tenant_context import TenantContextMiddleware
from ipe_shared.metrics import setup_metrics
from ipe_shared.observability import setup_observability


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging

    logger = logging.getLogger(settings.SERVICE_NAME)
    await init_database(settings.DATABASE_URL)
    await start_consumers()
    # Fix 2D: pre-import statsmodels/scipy to avoid cold-start on first best_fit
    try:
        import statsmodels.tsa.arima.model  # noqa: F401
        import statsmodels.tsa.holtwinters  # noqa: F401
        from scipy import stats  # noqa: F401

        logger.info("statsmodels warm-up complete")
    except ImportError:
        logger.warning("statsmodels not available — ARIMA/SARIMA disabled")
    yield
    await stop_consumers()
    await close_database()


def create_app() -> FastAPI:
    app = FastAPI(
        title="IPE - Demand Sensing & Forecasting",
        version=settings.VERSION,
        lifespan=lifespan,
    )
    setup_observability(app, service_name=settings.SERVICE_NAME)
    setup_metrics(app, service_name=settings.SERVICE_NAME, version="9.3.0-p2")
    app.add_middleware(TenantContextMiddleware)
    setup_cors(app)
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
