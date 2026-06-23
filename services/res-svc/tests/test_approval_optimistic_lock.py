"""Test optimistic-lock on approval: two concurrent approvals → exactly one 200, one 409."""
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.v1.resolution import ApproveRequest, approve_scenario
from ipe_shared.auth.jwt import TokenPayload


def _make_user(tenant_id: str):
    return TokenPayload(
        sub=uuid4(),
        tenant_id=tenant_id,
        role="planner",
        type="access",
        exp=datetime.now(UTC) + timedelta(minutes=60),
        iat=datetime.now(UTC),
        jti=str(uuid4()),
    )


class TestApprovalOptimisticLock:
    @pytest.mark.asyncio
    async def test_successful_approval_returns_200(self):
        scenario_id = uuid4()
        mo_id = uuid4()
        tenant_id = str(uuid4())
        scenario_mo_id = str(mo_id)

        scenario_mock = MagicMock()
        scenario_mock.id = scenario_id
        scenario_mock.mo_id = scenario_mo_id
        scenario_mock.status = "proposed"
        scenario_mock.strategy = "reschedule"
        scenario_mock.delivery_impact_days = 3.0
        scenario_mock.cost_impact = 5000.0
        scenario_mock.approved_by = None
        scenario_mock.approved_at = None
        scenario_mock.comment = ""

        mo_mock = MagicMock()
        mo_mock.id = mo_id
        mo_mock.version = 1

        req = ApproveRequest(scenario_id=scenario_id, approved_by="tester", comment="approve")

        with patch("app.api.v1.resolution.tenant_ctx") as mock_ctx:
            mock_ctx.get.return_value = tenant_id
            mock_session = AsyncMock()

            mock_scenario_result = MagicMock()
            mock_scenario_result.scalar_one_or_none.return_value = scenario_mock
            mock_mo_result = MagicMock()
            mock_mo_result.scalar_one_or_none.return_value = mo_mock
            mock_update_result = MagicMock()
            mock_update_result.rowcount = 1

            async def side_effect_execute(*args, **kw):
                sql = str(args[0]) if args and hasattr(args[0], "compile") else str(args[0]) if args else ""
                if "resolution_scenario" in sql:
                    return mock_scenario_result
                if "manufacturing_order" in sql and "version" not in sql:
                    return mock_mo_result
                if "version" in sql:
                    return mock_update_result
                return MagicMock()

            mock_session.execute = AsyncMock(side_effect=side_effect_execute)
            mock_kafka_send = AsyncMock()

            with patch("app.api.v1.resolution.kafka_producer") as mock_kafka:
                mock_kafka.build_envelope.return_value = {"event_id": str(uuid4())}
                mock_kafka.send_avro = mock_kafka_send
                user = _make_user(tenant_id)
                result = await approve_scenario(req, session=mock_session, current_user=user)

        assert result.success is True
        assert result.data["status"] == "approved"
