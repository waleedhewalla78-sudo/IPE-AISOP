import pytest
from unittest.mock import patch, MagicMock

from ipe_shared.database.base import Base
from ipe_shared.database.connection import init_database, close_database, get_engine


class TestDatabaseBase:
    def test_base_metadata(self):
        assert hasattr(Base, "metadata")
        assert Base.metadata is not None


class TestDatabaseConnection:
    @patch("ipe_shared.database.connection._engine", None)
    async def test_get_engine_raises_when_not_initialized(self):
        with pytest.raises(RuntimeError, match="Database not initialized"):
            get_engine()

    @patch("ipe_shared.database.connection.create_async_engine")
    async def test_init_database(self, mock_create_engine):
        mock_engine = MagicMock()
        mock_sync_engine = MagicMock()
        mock_engine.sync_engine = mock_sync_engine
        mock_create_engine.return_value = mock_engine
        engine = await init_database("postgresql+asyncpg://test:test@localhost/test")
        assert engine is mock_engine

    @patch("ipe_shared.database.connection._engine", MagicMock())
    async def test_get_engine_returns_engine(self):
        engine = get_engine()
        assert engine is not None
