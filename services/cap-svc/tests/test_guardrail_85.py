"""Integration-style tests for feasibility guardrail on schedule approve."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.priority_resolver import FEASIBILITY_GUARDRAIL_THRESHOLD, passes_feasibility_guardrail
from app.core.schedule_persistence import approve_schedule_mos


def test_passes_feasibility_guardrail_at_threshold():
    assert passes_feasibility_guardrail(85.0) is True
    assert passes_feasibility_guardrail(84.9) is False
    assert passes_feasibility_guardrail(None) is True


@pytest.mark.asyncio
async def test_approve_blocks_low_feasibility_and_audits():
    session = AsyncMock()
    mo_id = uuid4()
    tenant_id = uuid4()

    mo = MagicMock()
    mo.version = 1
    mo.feasibility_score = 82.0
    mo.ai_suggested_start = datetime.now(UTC)
    mo.ai_suggested_end = datetime.now(UTC)

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = mo
    session.execute = AsyncMock(return_value=result_mock)

    with patch("app.core.schedule_persistence.log_audit_event", new_callable=AsyncMock) as audit:
        result = await approve_schedule_mos(session, tenant_id, [mo_id], approved_by="planner")

    assert result["activated_count"] == 0
    assert result["failed_count"] == 1
    assert result["failed"][0]["reason"] == "GUARDRAIL_FEASIBILITY"
    assert result["failed"][0]["threshold"] == FEASIBILITY_GUARDRAIL_THRESHOLD
    audit.assert_awaited_once()
    assert audit.await_args.kwargs["action"] == "autonomy_downgraded_to_suggest"
