import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from ipe_shared.database.session import get_session
from ipe_shared.middleware.tenant_context import tenant_ctx


class TestSession:
    @patch("ipe_shared.database.session.get_engine")
    @patch("ipe_shared.database.session.async_sessionmaker")
    async def test_set_local_when_tenant_set(self, mock_sessionmaker_cls, mock_get_engine):
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        mock_factory = MagicMock()
        mock_sessionmaker_cls.return_value = mock_factory

        mock_cm = MagicMock()
        mock_session = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock()
        mock_factory.return_value = mock_cm

        token = tenant_ctx.set("550e8400-e29b-41d4-a716-446655440000")
        try:
            async for session in get_session():
                pass
        finally:
            tenant_ctx.reset(token)

        mock_session.execute.assert_awaited_once()
        call_args = mock_session.execute.call_args
        assert "set_config" in str(call_args[0][0])

    @patch("ipe_shared.database.session.get_engine")
    @patch("ipe_shared.database.session.async_sessionmaker")
    async def test_skip_set_local_when_no_tenant(self, mock_sessionmaker_cls, mock_get_engine):
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        mock_factory = MagicMock()
        mock_sessionmaker_cls.return_value = mock_factory

        mock_cm = MagicMock()
        mock_session = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock()
        mock_factory.return_value = mock_cm

        async for session in get_session():
            pass

        mock_session.execute.assert_not_called()

    @patch("ipe_shared.database.session.get_engine")
    @patch("ipe_shared.database.session.async_sessionmaker")
    async def test_yields_session_object(self, mock_sessionmaker_cls, mock_get_engine):
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        mock_factory = MagicMock()
        mock_sessionmaker_cls.return_value = mock_factory

        mock_cm = MagicMock()
        mock_session = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock()
        mock_factory.return_value = mock_cm

        async for session in get_session():
            assert session is mock_session
