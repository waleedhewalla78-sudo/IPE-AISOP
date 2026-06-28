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


V8_TENANT_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
_v8_session_store: dict = {}
_v8_session_singleton: AsyncMock | None = None


def reset_v8_test_session() -> None:
    global _v8_session_singleton
    _v8_session_store.clear()
    _v8_session_singleton = None


def make_v8_mock_session() -> AsyncMock:
    mock_session = make_mock_session()

    def _add(obj) -> None:
        _assign_id_on_add(obj)
        _v8_session_store[(type(obj), obj.id)] = obj

    async def _get(model, pk):
        key = (model, pk)
        if key in _v8_session_store:
            return _v8_session_store[key]
        try:
            from uuid import UUID

            alt = (model, UUID(str(pk)))
            return _v8_session_store.get(alt)
        except Exception:
            return None

    mock_session.add = MagicMock(side_effect=_add)
    mock_session.get = AsyncMock(side_effect=_get)
    return mock_session


def _assign_id_on_add(obj) -> None:
    if getattr(obj, "id", None) is None:
        obj.id = uuid4()


async def mock_v8_get_session() -> AsyncIterator:
    global _v8_session_singleton
    if _v8_session_singleton is None:
        _v8_session_singleton = make_v8_mock_session()
    yield _v8_session_singleton


def apply_v8_api_overrides(app, *, role: str = "planner") -> None:
    from uuid import UUID

    reset_v8_test_session()
    payload = make_token_payload(role=role, tenant_id=UUID(V8_TENANT_ID))

    async def _mock_current_user() -> TokenPayload:
        return payload

    app.dependency_overrides[get_current_user] = _mock_current_user
    app.dependency_overrides[get_session] = mock_v8_get_session


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
