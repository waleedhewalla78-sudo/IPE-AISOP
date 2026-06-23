"""Tests for IoT predictive maintenance and capacity degradation."""

from app.core.iot_health import (
    build_maintenance_block,
    calculate_capacity_degradation,
    calculate_operation_duration_impact,
    should_trigger_replan,
)


class TestCapacityDegradation:
    def test_full_capacity_above_80(self):
        result = calculate_capacity_degradation(85)
        assert result["capacity_factor"] == 1.0
        assert result["requires_maintenance"] is False
        assert result["status"] == "healthy"

    def test_degraded_capacity_50_to_80(self):
        result = calculate_capacity_degradation(65)
        assert result["capacity_factor"] == 0.85
        assert result["requires_maintenance"] is False
        assert result["status"] == "degraded"

    def test_maintenance_required_below_50(self):
        result = calculate_capacity_degradation(40)
        assert result["capacity_factor"] == 0.0
        assert result["requires_maintenance"] is True
        assert result["status"] == "maintenance_required"

    def test_boundary_80(self):
        result = calculate_capacity_degradation(80)
        assert result["capacity_factor"] == 0.85
        assert result["status"] == "degraded"

    def test_boundary_50(self):
        result = calculate_capacity_degradation(50)
        assert result["capacity_factor"] == 0.85
        assert result["status"] == "degraded"

    def test_boundary_49(self):
        result = calculate_capacity_degradation(49)
        assert result["requires_maintenance"] is True


class TestDurationImpact:
    def test_no_degradation(self):
        result = calculate_operation_duration_impact(60, 1.0)
        assert result == 60

    def test_degraded_capacity(self):
        result = calculate_operation_duration_impact(60, 0.85)
        assert result == 70

    def test_zero_capacity(self):
        result = calculate_operation_duration_impact(60, 0.0)
        assert result == 60


class TestShouldTriggerReplan:
    def test_no_previous_health(self):
        result = should_trigger_replan(None, 85)
        assert result["should_replan"] is False

    def test_initial_maintenance(self):
        result = should_trigger_replan(None, 30)
        assert result["should_replan"] is True
        assert result["severity"] == "high"

    def test_health_drop_to_maintenance(self):
        result = should_trigger_replan(70, 40)
        assert result["should_replan"] is True
        assert result["severity"] == "high"

    def test_capacity_factor_drop(self):
        result = should_trigger_replan(85, 55, previous_factor=1.0)
        assert result["should_replan"] is True
        assert result["severity"] == "medium"

    def test_no_significant_change(self):
        result = should_trigger_replan(90, 85, previous_factor=1.0)
        assert result["should_replan"] is False

    def test_status_change(self):
        result = should_trigger_replan(85, 75)
        assert result["should_replan"] is True


class TestMaintenanceBlock:
    def test_build_maintenance_block(self):
        block = build_maintenance_block("WC1", "tenant1", 45)
        assert block["work_center_id"] == "WC1"
        assert block["tenant_id"] == "tenant1"
        assert block["duration_planned_mins"] == 240
        assert block["is_maintenance_block"] is True
        assert block["priority_score"] == 999


class TestIoTTelemetryAPI:
    """API-level tests for IoT telemetry endpoint."""

    def test_telemetry_no_tenant_returns_error(self):
        from fastapi.testclient import TestClient
        from app.main import create_app
        app = create_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post(
            "/api/v1/iot/telemetry",
            json={"resource_id": "WC1", "health_score": 75},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "NO_TENANT"

    def test_health_endpoint_no_tenant_returns_error(self):
        from fastapi.testclient import TestClient
        from app.main import create_app
        app = create_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/iot/health/WC1")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "NO_TENANT"
