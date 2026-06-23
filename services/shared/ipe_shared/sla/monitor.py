"""SLA monitoring and uptime tracking for IPE.

Tracks service availability, response times, and computes SLA credits.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("ipe.sla")


@dataclass
class SLATarget:
    name: str
    target_uptime_pct: float
    measurement_window_days: int
    error_budget_minutes: float
    penalty_per_percent: float  # credit % per 1% downtime below target


@dataclass
class ServiceHealth:
    service_name: str
    total_checks: int = 0
    successful_checks: int = 0
    failed_checks: int = 0
    last_check_at: str = ""
    last_failure_at: str = ""

    @property
    def uptime_pct(self) -> float:
        if self.total_checks == 0:
            return 100.0
        return (self.successful_checks / self.total_checks) * 100

    @property
    def is_healthy(self) -> bool:
        return self.uptime_pct >= 99.9


@dataclass
class SLAViolation:
    service_name: str
    violation_type: str  # "uptime", "latency", "error_rate"
    actual_value: float
    target_value: float
    detected_at: str = ""
    resolved_at: str = ""
    credit_pct: float = 0.0

    def __post_init__(self) -> None:
        if not self.detected_at:
            self.detected_at = datetime.now(UTC).isoformat()


@dataclass
class SLAReport:
    period_start: str = ""
    period_end: str = ""
    services: dict[str, ServiceHealth] = field(default_factory=dict)
    violations: list[SLAViolation] = field(default_factory=list)
    total_uptime_pct: float = 100.0
    credit_amount: float = 0.0

    @property
    def overall_status(self) -> str:
        if self.total_uptime_pct >= 99.9:
            return "healthy"
        if self.total_uptime_pct >= 99.0:
            return "degraded"
        return "critical"


IPE_SLA_TARGETS: dict[str, SLATarget] = {
    "platform": SLATarget("Platform Overall", 99.9, 30, 43.2, 5.0),
    "dpe-svc": SLATarget("Demand Planning Engine", 99.9, 30, 43.2, 5.0),
    "mat-svc": SLATarget("Material Availability", 99.9, 30, 43.2, 5.0),
    "cap-svc": SLATarget("Capacity Scheduling", 99.95, 30, 21.6, 10.0),
    "fea-svc": SLATarget("Feasibility Scoring", 99.9, 30, 43.2, 5.0),
    "res-svc": SLATarget("Resolution Engine", 99.5, 30, 216.0, 2.0),
    "nlp-svc": SLATarget("NLP Copilot", 99.0, 30, 432.0, 1.0),
    "alert-svc": SLATarget("Alert Manager", 99.99, 30, 4.32, 20.0),
}


class SLAMonitor:
    def __init__(self) -> None:
        self._health: dict[str, ServiceHealth] = {}
        self._violations: list[SLAViolation] = []
        self._check_history: list[dict[str, Any]] = []

    def record_check(self, service_name: str, success: bool, latency_ms: float = 0) -> None:
        if service_name not in self._health:
            self._health[service_name] = ServiceHealth(service_name=service_name)

        h = self._health[service_name]
        h.total_checks += 1
        h.last_check_at = datetime.now(UTC).isoformat()
        if success:
            h.successful_checks += 1
        else:
            h.failed_checks += 1
            h.last_failure_at = datetime.now(UTC).isoformat()

        self._check_history.append({
            "service": service_name,
            "success": success,
            "latency_ms": latency_ms,
            "timestamp": h.last_check_at,
        })

        target = IPE_SLA_TARGETS.get(service_name)
        if target and h.total_checks >= 100 and h.uptime_pct < target.target_uptime_pct:
            violation = SLAViolation(
                service_name=service_name,
                violation_type="uptime",
                actual_value=h.uptime_pct,
                target_value=target.target_uptime_pct,
                credit_pct=max(0, (target.target_uptime_pct - h.uptime_pct) * target.penalty_per_percent),
            )
            self._violations.append(violation)
            logger.warning(
                "SLA violation: %s uptime %.2f%% < target %.2f%% (credit %.1f%%)",
                service_name, h.uptime_pct, target.target_uptime_pct, violation.credit_pct,
            )

    def get_service_health(self, service_name: str) -> ServiceHealth | None:
        return self._health.get(service_name)

    def get_report(self) -> SLAReport:
        now = datetime.now(UTC)
        total_checks = sum(h.total_checks for h in self._health.values())
        total_success = sum(h.successful_checks for h in self._health.values())
        overall_uptime = (total_success / total_checks * 100) if total_checks > 0 else 100.0

        return SLAReport(
            period_start=now.replace(day=1).isoformat(),
            period_end=now.isoformat(),
            services=dict(self._health),
            violations=self._violations,
            total_uptime_pct=overall_uptime,
            credit_amount=sum(v.credit_pct for v in self._violations),
        )

    def get_uptime_summary(self) -> dict[str, float]:
        return {name: h.uptime_pct for name, h in self._health.items()}


_sla_monitor: SLAMonitor | None = None


def get_sla_monitor() -> SLAMonitor:
    global _sla_monitor
    if _sla_monitor is None:
        _sla_monitor = SLAMonitor()
    return _sla_monitor
