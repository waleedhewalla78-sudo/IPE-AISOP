import pytest
from uuid import uuid4
from httpx import AsyncClient, ASGITransport

from ipe_shared.auth.jwt import create_access_token

TEST_TENANT_ID = uuid4()
TEST_USER_ID = uuid4()


@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def auth_headers():
    token = create_access_token(TEST_USER_ID, TEST_TENANT_ID, "planner")
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(TEST_TENANT_ID)}


@pytest.fixture
def admin_headers():
    token = create_access_token(TEST_USER_ID, TEST_TENANT_ID, "admin")
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(TEST_TENANT_ID)}
