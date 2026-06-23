import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from ipe_shared.audit.service import log_audit_event, create_audit_writer


class TestAuditService:
    @pytest.mark.asyncio
    async def test_log_audit_event_calls_session_execute(self):
        mock_session = AsyncMock()
        mock_factory = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))

        with patch("ipe_shared.audit.service.get_engine", return_value=MagicMock()), \
             patch("ipe_shared.audit.service.async_sessionmaker", return_value=mock_factory):
            await log_audit_event(
                tenant_id=uuid4(),
                actor_type="user",
                actor_id="user-123",
                action="APPROVE_SCHEDULE",
                entity_type="manufacturing_order",
                entity_id=uuid4(),
                before_state={"status": "proposed"},
                after_state={"status": "approved"},
                rationale="Test approval",
            )
            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_audit_event_handles_exception_gracefully(self):
        with patch("ipe_shared.audit.service.get_engine", side_effect=Exception("DB down")):
            await log_audit_event(
                tenant_id=uuid4(),
                actor_type="user",
                actor_id="user-123",
                action="TEST",
                entity_type="test",
                entity_id=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_create_audit_writer_returns_callable(self):
        writer = create_audit_writer(uuid4(), "user", "user-123")
        assert callable(writer)

    @pytest.mark.asyncio
    async def test_create_audit_writer_calls_log_audit_event(self):
        mock_session = AsyncMock()
        mock_factory = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))

        with patch("ipe_shared.audit.service.get_engine", return_value=MagicMock()), \
             patch("ipe_shared.audit.service.async_sessionmaker", return_value=mock_factory):
            writer = create_audit_writer(uuid4(), "user", "user-123")
            await writer("TEST_ACTION", "test_entity", uuid4())
            mock_session.execute.assert_called_once()
