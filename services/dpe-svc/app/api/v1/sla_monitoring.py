"""SLA monitoring API endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from ipe_shared.sla.monitor import get_sla_monitor, IPE_SLA_TARGETS

router = APIRouter(prefix="/sla", tags=["sla"])


@router.get("/targets")
async def list_sla_targets() -> dict:
    return {
        "targets": {
            name: {
                "name": t.name,
                "target_uptime_pct": t.target_uptime_pct,
                "measurement_window_days": t.measurement_window_days,
                "error_budget_minutes": t.error_budget_minutes,
            }
            for name, t in IPE_SLA_TARGETS.items()
        }
    }


@router.get("/health")
async def get_service_health() -> dict:
    monitor = get_sla_monitor()
    report = monitor.get_report()
    return {
        "overall_uptime_pct": report.total_uptime_pct,
        "overall_status": report.overall_status,
        "credit_amount": report.credit_amount,
        "services": {
            name: {"uptime_pct": h.uptime_pct, "total_checks": h.total_checks, "failed": h.failed_checks}
            for name, h in report.services.items()
        },
    }


@router.get("/report")
async def get_sla_report() -> dict:
    monitor = get_sla_monitor()
    report = monitor.get_report()
    return {
        "period_start": report.period_start,
        "period_end": report.period_end,
        "total_uptime_pct": report.total_uptime_pct,
        "overall_status": report.overall_status,
        "violations": [
            {"service": v.service_name, "type": v.violation_type, "actual": v.actual_value, "target": v.target_value}
            for v in report.violations
        ],
        "credit_amount": report.credit_amount,
    }


@router.get("/credits")
async def compute_sla_credits() -> dict:
    monitor = get_sla_monitor()
    report = monitor.get_report()
    if report.credit_amount > 0:
        return {
            "credits_applicable": True,
            "credit_pct": report.credit_amount,
            "reason": "SLA uptime below target",
            "violations": len(report.violations),
        }
    return {"credits_applicable": False, "credit_pct": 0.0}
