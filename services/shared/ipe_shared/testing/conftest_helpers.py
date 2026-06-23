"""Shared FastAPI test helpers for IPE microservices."""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

from ipe_shared.auth.dependencies import get_current_user
from ipe_shared.auth.jwt import TokenPayload, create_access_token
from ipe_shared.database.session import get_session

DEFAULT_JWT_SECRET = "dev-jwt-secret-change-in-production-min-32-chars"


def make_token_payload(
    *,
    role: str = "admin",
    user_id: UUID | None = None,
    tenant_id: UUID | None = None,
) -> TokenPayload:
    uid = user_id or uuid4()
    tid = tenant_id or uuid4()
    return TokenPayload(sub=str(uid), tenant_id=str(tid), role=role, type="access")


async def mock_get_session() -> AsyncIterator:
    yield make_mock_session()


def make_mock_session() -> AsyncMock:
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_scalars.one_or_none.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_result.scalar_one_or_none.return_value = None
    mock_result.one_or_none.return_value = None
    mock_result.fetchone.return_value = (None,)
    mock_result.fetchall.return_value = []
    mock_result.scalar.return_value = 0
    mock_result.one.return_value = MagicMock(on_time=0, total=0)
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.flush = AsyncMock()
    return mock_session


def apply_session_override(app) -> None:
    app.dependency_overrides[get_session] = mock_get_session


def apply_auth_and_session_overrides(
    app,
    *,
    role: str = "admin",
    user_id: UUID | None = None,
    tenant_id: UUID | None = None,
) -> None:
    payload = make_token_payload(role=role, user_id=user_id, tenant_id=tenant_id)

    async def _mock_current_user() -> TokenPayload:
        return payload

    app.dependency_overrides[get_current_user] = _mock_current_user
    apply_session_override(app)


def clear_overrides(app) -> None:
    app.dependency_overrides.clear()


def make_auth_headers(
    *,
    role: str = "planner",
    user_id: UUID | None = None,
    tenant_id: UUID | None = None,
    include_tenant_header: bool = True,
) -> dict[str, str]:
    uid = user_id or uuid4()
    tid = tenant_id or uuid4()
    token = create_access_token(user_id=uid, tenant_id=tid, role=role)
    headers = {"Authorization": f"Bearer {token}"}
    if include_tenant_header:
        headers["X-Tenant-ID"] = str(tid)
    return headers
