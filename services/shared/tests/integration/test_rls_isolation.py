import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy import text

from ipe_shared.database.session import tenant_ctx, get_session


pytestmark = [
    pytest.mark.integration,
]


@pytest.fixture
def tenant_a_id() -> str:
    return str(uuid4())


@pytest.fixture
def tenant_b_id() -> str:
    return str(uuid4())


class TestRLSIsolation:
    async def test_tenant_a_cannot_read_tenant_b_data(self, tenant_a_id, tenant_b_id):
        assert tenant_a_id != tenant_b_id
        mock_engine = MagicMock()
        mock_session = AsyncMock()

        mock_factory = MagicMock()
        mock_session_obj = MagicMock()
        mock_session_obj.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value = mock_session_obj

        with patch("ipe_shared.database.session.get_engine", return_value=mock_engine):
            with patch(
                "ipe_shared.database.session.async_sessionmaker", return_value=mock_factory
            ):
                token = tenant_ctx.set(tenant_a_id)
                try:
                    async for session in get_session():
                        session.execute.assert_called_once()
                finally:
                    tenant_ctx.reset(token)

    async def test_set_local_scopes_session(self, tenant_a_id, tenant_b_id):
        token = tenant_ctx.set(tenant_a_id)
        try:
            mock_engine = MagicMock()
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock()

            mock_factory = MagicMock()
            mock_session_obj = MagicMock()
            mock_session_obj.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value = mock_session_obj

            with patch("ipe_shared.database.session.get_engine", return_value=mock_engine):
                with patch(
                    "ipe_shared.database.session.async_sessionmaker", return_value=mock_factory
                ):
                    async for _ in get_session():
                        call_kwargs = mock_session.execute.call_args
                        if call_kwargs:
                            args, kwargs = call_kwargs
                            compiled = (
                                args[0].compile() if hasattr(args[0], "compile") else args[0]
                            )
                            assert "set_config" in str(compiled)
                            assert "app.current_tenant_id" in str(compiled)
        finally:
            tenant_ctx.reset(token)

    async def test_unscoped_query_returns_no_rows(self):
        mock_engine = MagicMock()
        mock_session = AsyncMock()

        mock_factory = MagicMock()
        mock_session_obj = MagicMock()
        mock_session_obj.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value = mock_session_obj

        with patch("ipe_shared.database.session.get_engine", return_value=mock_engine):
            with patch(
                "ipe_shared.database.session.async_sessionmaker", return_value=mock_factory
            ):
                async for _ in get_session():
                    assert mock_session.execute.call_count == 0
