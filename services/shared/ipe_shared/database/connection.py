import logging
import os

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None

_DEFAULT_POOL_SIZE = 20
_DEFAULT_MAX_OVERFLOW = 10
_DEFAULT_STATEMENT_TIMEOUT_MS = 30_000


def _pool_size() -> int:
    return int(os.getenv("IPE_DB_POOL_SIZE", str(_DEFAULT_POOL_SIZE)))


def _max_overflow() -> int:
    return int(os.getenv("IPE_DB_MAX_OVERFLOW", str(_DEFAULT_MAX_OVERFLOW)))


def _statement_timeout_ms() -> int:
    return int(os.getenv("IPE_DB_STATEMENT_TIMEOUT_MS", str(_DEFAULT_STATEMENT_TIMEOUT_MS)))


async def init_database(database_url: str) -> AsyncEngine:
    global _engine
    from ipe_shared.startup import validate_startup_config

    validate_startup_config()
    pool_size = _pool_size()
    max_overflow = _max_overflow()
    if pool_size < 10:
        logger.warning(
            "DB pool_size=%s is below recommended minimum of 10 for concurrent workloads",
            pool_size,
        )

    _engine = create_async_engine(
        database_url,
        echo=False,
        pool_size=pool_size,
        max_overflow=max_overflow,
    )

    timeout_ms = _statement_timeout_ms()

    @event.listens_for(_engine.sync_engine, "connect")
    def _set_statement_timeout(dbapi_conn, connection_record):
        try:
            with dbapi_conn.cursor() as cur:
                cur.execute(f"SET statement_timeout = '{timeout_ms}'")
        except Exception as e:
            logger.debug("Could not set statement_timeout: %s", e)

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

    logger.info(
        "Database pool initialized (pool_size=%s, max_overflow=%s, statement_timeout_ms=%s)",
        pool_size,
        max_overflow,
        timeout_ms,
    )
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
