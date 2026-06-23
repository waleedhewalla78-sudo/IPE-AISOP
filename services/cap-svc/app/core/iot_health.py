"""IoT predictive maintenance: health-to-capacity mapping and degradation logic."""

from datetime import UTC, datetime


HEALTH_FULL_CAPACITY_THRESHOLD = 80
HEALTH_DEGRADED_THRESHOLD = 50
FULL_CAPACITY_FACTOR = 1.0
DEGRADED_CAPACITY_FACTOR = 0.85


def calculate_capacity_degradation(health_score: float) -> dict:
    """Map machine health score to capacity degradation factor.

    Rules:
        - Health > 80: 100% capacity (full speed)
        - Health 50-80: 85% capacity (slower cycle times)
        - Health < 50: Trigger preventative maintenance block

    Args:
        health_score: Machine health score on 0-100 scale.

    Returns:
        Dict with capacity_factor, requires_maintenance, and degradation_pct.
    """
    if health_score > HEALTH_FULL_CAPACITY_THRESHOLD:
        return {
            "capacity_factor": FULL_CAPACITY_FACTOR,
            "requires_maintenance": False,
            "degradation_pct": 0.0,
            "status": "healthy",
        }

    if health_score >= HEALTH_DEGRADED_THRESHOLD:
        degradation_pct = round((1.0 - DEGRADED_CAPACITY_FACTOR) * 100, 2)
        return {
            "capacity_factor": DEGRADED_CAPACITY_FACTOR,
            "requires_maintenance": False,
            "degradation_pct": degradation_pct,
            "status": "degraded",
        }

    return {
        "capacity_factor": 0.0,
        "requires_maintenance": True,
        "degradation_pct": 100.0,
        "status": "maintenance_required",
    }


def calculate_operation_duration_impact(
    original_duration_mins: int,
    capacity_factor: float,
) -> int:
    """Calculate new operation duration based on capacity degradation.

    When capacity drops, operations take longer (inverse relationship).
    """
    if capacity_factor <= 0:
        return original_duration_mins

    return max(1, int(original_duration_mins / capacity_factor))


def should_trigger_replan(
    previous_health: float | None,
    current_health: float,
    previous_factor: float | None = None,
) -> dict:
    """Determine if health change should trigger a replan.

    Triggers replan if:
    - Capacity drops by more than 15%
    - Machine transitions to maintenance_required state

    Returns:
        Dict with should_replan, reason, and severity.
    """
    if previous_health is None:
        if current_health < HEALTH_DEGRADED_THRESHOLD:
            return {
                "should_replan": True,
                "reason": "Initial health reading indicates maintenance required",
                "severity": "high",
            }
        return {"should_replan": False, "reason": "Initial reading within normal range", "severity": "low"}

    current_result = calculate_capacity_degradation(current_health)
    previous_result = calculate_capacity_degradation(previous_health) if previous_health is not None else None

    if current_result["requires_maintenance"]:
        return {
            "should_replan": True,
            "reason": f"Health dropped to {current_health}, maintenance required",
            "severity": "high",
        }

    if previous_factor is not None:
        factor_drop = previous_factor - current_result["capacity_factor"]
        if factor_drop > 0.15:
            return {
                "should_replan": True,
                "reason": f"Capacity factor dropped by {factor_drop:.0%} (from {previous_factor:.0%} to {current_result['capacity_factor']:.0%})",
                "severity": "medium",
            }

    if previous_result and previous_result["status"] != current_result["status"]:
        return {
            "should_replan": True,
            "reason": f"Health status changed from {previous_result['status']} to {current_result['status']}",
            "severity": "medium",
        }

    return {"should_replan": False, "reason": "Health change within normal range", "severity": "low"}


def build_maintenance_block(
    resource_id: str,
    tenant_id: str,
    health_score: float,
    maintenance_duration_hours: int = 4,
) -> dict:
    """Build a maintenance operation block for scheduling.

    This creates a dummy operation that blocks the resource for maintenance.
    """
    now = datetime.now(UTC)
    return {
        "id": f"MAINT_{resource_id}_{int(now.timestamp())}",
        "mo_id": f"MAINT_{resource_id}",
        "sequence": 0,
        "work_center_id": resource_id,
        "duration_planned_mins": maintenance_duration_hours * 60,
        "operation_name": f"Preventative Maintenance - Health {health_score:.0f}",
        "due_date_minutes": maintenance_duration_hours * 60 + 60,
        "priority_score": 999,
        "material_score": 1.0,
        "requires_operator": False,
        "is_maintenance_block": True,
        "tenant_id": tenant_id,
    }
