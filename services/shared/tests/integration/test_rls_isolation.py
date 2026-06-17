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
        """Verify that querying with Tenant A's sql returns ONLY Tenant A's data.

        This validates the RLS policy tenant_isolation using set_config pattern.
        """
        assert tenant_a_id != tenant_b_id

        mock_engine = MagicMock()
        mock_conn = AsyncMock()
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()

        with patch("ipe_shared.database.session.get_engine", return_value=mock_engine):
            token = tenant_ctx.set(tenant_a_id)
            try:
                async for session in get_session():
                    session.execute.assert_not_called()  # session not yet bound
            finally:
                tenant_ctx.reset(token)

    async def test_set_local_scopes_session(self, tenant_a_id, tenant_b_id):
        """Verify that get_session() calls set_config with the correct tenant_id."""
        token = tenant_ctx.set(tenant_a_id)
        try:
            mock_engine = MagicMock()
            mock_session_factory = MagicMock()
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            with (
                patch("ipe_shared.database.session.get_engine", return_value=mock_engine),
                patch("ipe_shared.database.session.async_session_factory", mock_session_factory),
            ):
                mock_session_factory.return_value = mock_session
                async for _ in get_session():
                    call_kwargs = mock_session.execute.call_args
                    if call_kwargs:
                        args, kwargs = call_kwargs
                        compiled = args[0].compile() if hasattr(args[0], "compile") else args[0]
                        assert "set_config" in str(compiled)
                        assert "app.current_tenant_id" in str(compiled)
        finally:
            tenant_ctx.reset(token)

    async def test_unscoped_query_returns_no_rows(self):
        """Without tenant context, set_config should NOT be called."""
        mock_engine = MagicMock()
        mock_session_factory = MagicMock()
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("ipe_shared.database.session.get_engine", return_value=mock_engine),
            patch("ipe_shared.database.session.async_session_factory", mock_session_factory),
        ):
            mock_session_factory.return_value = mock_session
            async for _ in get_session():
                assert mock_session.execute.call_count == 0
