"""Test fea-svc dual gate: does NOT score until BOTH material_scored AND capacity_scored arrive.

Tests the _score_and_publish function directly (the core gating logic).
"""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_score_and_publish_skips_when_mat_score_none():
    from app.events.handlers import _score_and_publish

    mock_session = AsyncMock()
    with patch("app.events.handlers.kafka_producer") as mock_kafka:
        await _score_and_publish(mock_session, str(uuid4()), str(uuid4()), None, 85.0)
        mock_kafka.send_avro.assert_not_called()


@pytest.mark.asyncio
async def test_score_and_publish_skips_when_cap_score_none():
    from app.events.handlers import _score_and_publish

    mock_session = AsyncMock()
    with patch("app.events.handlers.kafka_producer") as mock_kafka:
        await _score_and_publish(mock_session, str(uuid4()), str(uuid4()), 0.85, None)
        mock_kafka.send_avro.assert_not_called()


@pytest.mark.asyncio
async def test_score_and_publish_publishes_when_both_present():
    from app.events.handlers import _score_and_publish

    mo_id = str(uuid4())
    tenant_id = str(uuid4())
    mock_session = AsyncMock()

    async def mock_exec(*args, **kw):
        sql = str(args[0]) if hasattr(args[0], "compile") else str(args[0]) if args else ""
        fake = MagicMock()
        if "status, product_id" in sql or ("FROM cdm_manufacturing_order" in sql and "bom_id" not in sql):
            fake.one_or_none.return_value = ("released", uuid4())
        elif "cdm_bill_of_material" in sql:
            fake.scalar_one_or_none.return_value = 1
        elif "cdm_routing_operation" in sql or "cdm_work_order" in sql:
            fake.fetchall.return_value = []
            fake.scalar.return_value = 0
            fake.one_or_none.return_value = None
        elif "cdm_work_center" in sql or "cdm_operator" in sql:
            fake.fetchall.return_value = []
            fake.one_or_none.return_value = None
        else:
            fake.scalar_one_or_none.return_value = None
        return fake

    mock_session.execute = AsyncMock(side_effect=mock_exec)
    mock_session.commit = AsyncMock()

    with patch("app.events.handlers.kafka_producer") as mock_kafka:
        mock_kafka.build_envelope.return_value = {"event_id": "test"}
        mock_kafka.send_avro = AsyncMock()
        await _score_and_publish(mock_session, mo_id, tenant_id, 0.85, 85.0)
        assert mock_kafka.build_envelope.called
        assert mock_kafka.send_avro.called
