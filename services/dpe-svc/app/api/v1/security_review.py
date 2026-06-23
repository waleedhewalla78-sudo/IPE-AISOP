"""ISO 27001 ISMS API endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from ipe_shared.compliance.iso27001 import get_isms_report

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/iso27001/report")
async def get_iso27001_report() -> dict:
    report = get_isms_report()
    return {
        "generated_at": report.generated_at,
        "total_controls": report.total_controls,
        "implemented": report.implemented,
        "partial": report.partial,
        "planned": report.planned,
        "not_applicable": report.not_applicable,
        "compliance_pct": report.compliance_pct,
        "risks": [
            {
                "risk_id": r.risk_id,
                "description": r.description,
                "risk_level": r.risk_level.value,
                "risk_score": r.risk_score,
                "mitigation": r.mitigation,
            }
            for r in report.risks
        ],
    }


@router.get("/security/review")
async def get_security_review() -> dict:
    from ipe_shared.security.review import generate_security_review_report
    report = generate_security_review_report()
    return {
        "generated_at": report.generated_at,
        "overall_risk": report.overall_risk,
        "total_findings": report.total_findings,
        "critical": report.critical,
        "high": report.high,
        "medium": report.medium,
        "low": report.low,
        "passed_checks": report.passed_checks,
        "failed_checks": report.failed_checks,
        "checks": report.checks,
    }
