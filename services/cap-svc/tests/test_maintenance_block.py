"""Tests for V6-R4 predictive maintenance blocks."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.maintenance_blocks import (
    RUL_MAINTENANCE_THRESHOLD_HOURS,
    block_to_operation,
    clear_maintenance_blocks,
    compute_block_window,
    get_active_maintenance_blocks,
    inject_maintenance_block_operations,
    register_maintenance_block,
)
from app.events.handlers import handle_maintenance_block_required


TENANT_ID = str(uuid4())
WC_ID = str(uuid4())


@pytest.fixture(autouse=True)
def _clear_blocks():
    clear_maintenance_blocks()
    yield
    clear_maintenance_blocks()


class TestMaintenanceBlockCore:
    def test_rul_threshold_constant(self):
        assert RUL_MAINTENANCE_THRESHOLD_HOURS == 48

    def test_compute_block_window_24h_duration(self):
        recorded = datetime(2026, 6, 23, 10, 0, tzinfo=UTC)
        start, end = compute_block_window(recorded, rul_hours=36)
        assert (end - start).total_seconds() == 24 * 3600

    def test_register_and_retrieve_block(self):
        start = datetime.now(UTC)
        end = start + timedelta(hours=24)
        register_maintenance_block(TENANT_ID, "CNC-04", WC_ID, start, end, 36)
        blocks = get_active_maintenance_blocks(TENANT_ID)
        assert len(blocks) == 1
        assert blocks[0]["machine_id"] == "CNC-04"

    def test_inject_maintenance_block_operations(self):
        start = datetime.now(UTC)
        end = start + timedelta(hours=24)
        register_maintenance_block(TENANT_ID, "CNC-04", WC_ID, start, end, 36)
        ops = [{"id": "op1", "mo_id": "mo1", "work_center_id": WC_ID, "duration_planned_mins": 60, "sequence": 1}]
        merged_ops, frozen = inject_maintenance_block_operations(ops, [], TENANT_ID)
        assert len(merged_ops) == 2
        assert len(frozen) == 1
        maint = next(op for op in merged_ops if op.get("is_maintenance_block"))
        assert maint["work_center_id"] == WC_ID

    def test_block_to_operation_fixed_interval(self):
        start = datetime(2026, 6, 24, 8, 0, tzinfo=UTC)
        end = start + timedelta(hours=24)
        block = register_maintenance_block(TENANT_ID, "CNC-04", WC_ID, start, end, 36)
        op = block_to_operation(block, horizon_start=datetime(2026, 6, 23, 10, 0, tzinfo=UTC))
        assert op["fixed_start"] >= 0
        assert op["duration_planned_mins"] == 24 * 60


class TestPredictiveTelemetryAPI:
    @pytest.mark.asyncio
    async def test_rul_36h_publishes_maintenance_block(self):
        from httpx import ASGITransport, AsyncClient

        from app.main import create_app
        from ipe_shared.middleware.tenant_context import tenant_ctx
        from ipe_shared.testing.conftest_helpers import apply_auth_and_session_overrides

        app = create_app()
        apply_auth_and_session_overrides(app)

        wc = MagicMock()
        wc.id = uuid4()
        wc.erp_source_id = "CNC-04"
        wc.name = "CNC-04"

        mock_session = AsyncMock()
        wc_result = MagicMock()
        wc_result.scalar_one_or_none.return_value = wc
        mock_session.execute = AsyncMock(return_value=wc_result)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        from ipe_shared.database.session import get_session as get_db_session

        async def override_session():
            yield mock_session

        app.dependency_overrides[get_db_session] = override_session

        token = tenant_ctx.set(TENANT_ID)
        transport = ASGITransport(app=app)
        with patch("app.api.v1.iot.kafka_producer.send_avro", new_callable=AsyncMock) as mock_avro:
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(
                    "/api/v1/iot/telemetry",
                    json={
                        "machine_id": "CNC-04",
                        "rul_hours": 36,
                        "vibration_rms": 2.1,
                        "recorded_at": "2026-06-23T10:00:00Z",
                    },
                    headers={"X-Tenant-ID": TENANT_ID},
                )
        tenant_ctx.reset(token)

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["maintenance_block_published"] is True
        mock_avro.assert_awaited_once()
        assert mock_avro.await_args.args[0] == "ipe.maintenance.block_required"

    @pytest.mark.asyncio
    async def test_rul_above_threshold_no_kafka(self):
        from httpx import ASGITransport, AsyncClient

        from app.main import create_app
        from ipe_shared.middleware.tenant_context import tenant_ctx
        from ipe_shared.testing.conftest_helpers import apply_auth_and_session_overrides

        app = create_app()
        apply_auth_and_session_overrides(app)

        wc = MagicMock()
        wc.id = uuid4()

        mock_session = AsyncMock()
        wc_result = MagicMock()
        wc_result.scalar_one_or_none.return_value = wc
        mock_session.execute = AsyncMock(return_value=wc_result)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        from ipe_shared.database.session import get_session as get_db_session

        async def override_session():
            yield mock_session

        app.dependency_overrides[get_db_session] = override_session

        token = tenant_ctx.set(TENANT_ID)
        transport = ASGITransport(app=app)
        with patch("app.api.v1.iot.kafka_producer.send_avro", new_callable=AsyncMock) as mock_avro:
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(
                    "/api/v1/iot/telemetry",
                    json={"machine_id": "CNC-04", "rul_hours": 72},
                    headers={"X-Tenant-ID": TENANT_ID},
                )
        tenant_ctx.reset(token)

        assert resp.status_code == 200
        assert resp.json()["data"]["maintenance_block_published"] is False
        mock_avro.assert_not_awaited()


class TestMaintenanceBlockHandler:
    @pytest.mark.asyncio
    async def test_handle_maintenance_block_triggers_partial_reschedule(self):
        payload = {
            "tenant_id": TENANT_ID,
            "machine_id": "CNC-04",
            "work_center_id": WC_ID,
            "block_start": "2026-06-24T08:00:00Z",
            "block_end": "2026-06-25T08:00:00Z",
            "rul_hours": 36,
        }
        with patch(
            "app.core.maintenance_blocks.partial_reschedule_for_block",
            new_callable=AsyncMock,
            return_value={"solver_status": "OPTIMAL", "affected_mo_ids": ["mo-1"], "assignments": []},
        ) as mock_reschedule:
            with patch("app.events.handlers.kafka_producer.send_event", new_callable=AsyncMock) as mock_send:
                await handle_maintenance_block_required({"payload": payload, "tenant_id": TENANT_ID})
                mock_reschedule.assert_awaited_once()
                mock_send.assert_awaited_once()
                assert mock_send.await_args.kwargs["value"]["data"]["replan_reason"] == "maintenance_block_required"
