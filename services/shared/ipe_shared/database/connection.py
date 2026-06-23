import logging

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None


async def init_database(database_url: str) -> AsyncEngine:
    global _engine
    _engine = create_async_engine(database_url, echo=False, pool_size=20, max_overflow=10)

    # CRITICAL: Reset tenant context on connection checkout to prevent cross-request leakage
    try:

        @event.listens_for(_engine.sync_engine, "checkout")
        def set_tenant_context(dbapi_conn, connection_record, connection_proxy):
            try:
                dbapi_conn.execute("SELECT set_config('app.current_tenant_id', '', false)")
            except (AttributeError, NotImplementedError) as e:
                logger.debug("Tenant context reset on checkout not supported: %s", e)
    except Exception as e:
        logger.warning("Failed to register connection checkout event listener: %s", e)

    return _engine


async def close_database():
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _engine
