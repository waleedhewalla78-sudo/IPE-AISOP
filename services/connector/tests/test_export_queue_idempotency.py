"""Test export queue idempotency: duplicate event → single row."""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

import pytest

from app.events.handlers import handle_resolution_approved
from ipe_shared.events.schemas import EventEnvelope


class TestExportQueueIdempotency:
    @pytest.mark.asyncio
    async def test_duplicate_event_does_not_create_second_row(self):
        event_id = str(uuid4())
        mo_id = str(uuid4())
        tenant_id = str(uuid4())

        envelope = EventEnvelope(
            event_id=event_id,
            event_type="ipe.resolution.approved",
            source="res-svc",
            tenant_id=UUID(tenant_id),
            timestamp="2026-06-17T00:00:00Z",
            data={
                "mo_id": mo_id,
                "scenario_id": str(uuid4()),
                "strategy": "reschedule",
                "approved_by": "tester",
                "delivery_impact_days": 3.0,
                "cost_impact": 5000.0,
            },
        )

        mock_event = MagicMock()
        mock_event.value = envelope.model_dump(mode="json")

        with patch("app.events.handlers._parse_event", return_value=envelope):
            with patch("app.events.handlers.get_engine"):
                with patch("app.events.handlers.async_sessionmaker") as ase:
                    mock_session = AsyncMock()
                    mock_existing = MagicMock()
                    mock_existing.scalar_one_or_none.return_value = 1  # row exists
                    mock_session.execute = AsyncMock(return_value=mock_existing)
                    ase.return_value.return_value.__aenter__.return_value = mock_session

                    with patch("app.events.handlers.logger") as mock_logger:
                        await handle_resolution_approved(mock_event)

                    mock_logger.info.assert_called_once()
                    assert "Duplicate" in mock_logger.info.call_args[0][0]

    @pytest.mark.asyncio
    async def test_first_event_creates_export_row(self):
        event_id = str(uuid4())
        mo_id = str(uuid4())
        tenant_id = str(uuid4())

        envelope = EventEnvelope(
            event_id=event_id,
            event_type="ipe.resolution.approved",
            source="res-svc",
            tenant_id=UUID(tenant_id),
            timestamp="2026-06-17T00:00:00Z",
            data={
                "mo_id": mo_id,
                "scenario_id": str(uuid4()),
                "strategy": "expedite",
                "approved_by": "planner",
                "delivery_impact_days": 1.0,
                "cost_impact": 2000.0,
            },
        )

        mock_event = MagicMock()
        mock_event.value = envelope.model_dump(mode="json")

        with patch("app.events.handlers._parse_event", return_value=envelope):
            with patch("app.events.handlers.get_engine"):
                with patch("app.events.handlers.async_sessionmaker") as ase:
                    mock_session = AsyncMock()
                    mock_existing = MagicMock()
                    mock_existing.scalar_one_or_none.return_value = None
                    mock_session.execute = AsyncMock(return_value=mock_existing)
                    ase.return_value.return_value.__aenter__.return_value = mock_session

                    await handle_resolution_approved(mock_event)

                    assert mock_session.execute.called
                    mock_session.commit.assert_called_once()
