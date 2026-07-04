"""Fixtures for cross-tenant security tests."""

from __future__ import annotations

import os
import sys
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from helpers import ASYNC_DB_URL, connect_db

ROOT = Path(__file__).resolve().parents[2]
SHARED_ROOT = ROOT / "services" / "shared"
if str(SHARED_ROOT) not in sys.path:
    sys.path.insert(0, str(SHARED_ROOT))

from ipe_shared.testing.conftest_helpers import make_auth_headers

from helpers import TENANT_A, TENANT_B

os.environ.setdefault("IPE_JWT_SECRET_KEY", "dev-jwt-secret-change-in-production-min-32-chars")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("IPE_ENVIRONMENT", "development")
os.environ.setdefault("IPE_REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("IPE_DATABASE_URL", ASYNC_DB_URL)


@pytest.fixture
def auth_headers_a() -> dict[str, str]:
    return make_auth_headers(role="planner", tenant_id=UUID(TENANT_A))


@pytest.fixture
def auth_headers_b() -> dict[str, str]:
    return make_auth_headers(role="planner", tenant_id=UUID(TENANT_B))


@pytest.fixture
def db_conn() -> Iterator:
    connection = connect_db()
    connection.autocommit = False
    yield connection
    connection.rollback()
    connection.close()


@pytest.fixture
async def res_client(db_conn) -> AsyncIterator:
    res_root = ROOT / "services" / "res-svc"
    inserted = str(res_root) not in sys.path
    if inserted:
        sys.path.insert(0, str(res_root))
    os.environ["IPE_DATABASE_URL"] = ASYNC_DB_URL

    try:
        with (
            patch("ipe_shared.events.producer.kafka_producer") as mock_producer,
            patch("app.main.start_consumers", new=AsyncMock()),
            patch("app.main.stop_consumers", new=AsyncMock()),
        ):
            mock_producer.send_event = AsyncMock()
            from httpx import ASGITransport, AsyncClient

            from ipe_shared.database.connection import close_database, init_database

            from app.main import create_app

            await init_database(ASYNC_DB_URL)
            app = create_app()
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                yield client
            await close_database()
    finally:
        if inserted:
            sys.path.remove(str(res_root))
