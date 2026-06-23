"""Dependabot alert monitoring and auto-remediation integration.

Checks GitHub Dependabot alerts via API, categorizes by severity,
and prepares auto-remediation PRs for patch-level updates.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger("ipe.security.dependabot")


class AlertSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertState(StrEnum):
    OPEN = "open"
    DISMISSED = "dismissed"
    FIXED = "fixed"


@dataclass
class DependabotAlert:
    alert_id: int
    package_name: str
    ecosystem: str
    severity: AlertSeverity
    state: AlertState
    vulnerable_range: str
    patched_version: str | None = None
    summary: str = ""
    created_at: str = ""
    updated_at: str = ""
    security_advisory_url: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()


@dataclass
class DependabotReport:
    repository: str
    generated_at: str = ""
    total_alerts: int = 0
    open_alerts: int = 0
    critical_alerts: int = 0
    high_alerts: int = 0
    medium_alerts: int = 0
    low_alerts: int = 0
    auto_remediation_candidates: int = 0
    alerts: list[DependabotAlert] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.generated_at:
            self.generated_at = datetime.now(UTC).isoformat()

    @property
    def needs_immediate_action(self) -> bool:
        return self.critical_alerts > 0 or self.high_alerts > 0


def categorize_alerts(alerts: list[DependabotAlert]) -> dict[str, list[DependabotAlert]]:
    """Categorize alerts by severity for prioritized remediation."""
    categories: dict[str, list[DependabotAlert]] = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": [],
    }
    for alert in alerts:
        categories[alert.severity.value].append(alert)
    return categories


def identify_auto_remediation_candidates(alerts: list[DependabotAlert]) -> list[DependabotAlert]:
    """Alerts eligible for auto-remediation (patch-level updates only)."""
    candidates = []
    for alert in alerts:
        if alert.state != AlertState.OPEN:
            continue
        if alert.patched_version and _is_patch_update(alert.vulnerable_range, alert.patched_version):
            candidates.append(alert)
    return candidates


def _is_patch_update(vulnerable_range: str, patched_version: str) -> bool:
    """Check if the fix is a patch-level update (not major/minor bump)."""
    try:
        vuln_parts = vulnerable_range.lstrip(">=<~^!").split(".")
        patch_parts = patched_version.split(".")
        if len(vuln_parts) >= 2 and len(patch_parts) >= 2:
            return vuln_parts[0] == patch_parts[0] and vuln_parts[1] == patch_parts[1]
    except (ValueError, IndexError):
        pass
    return False


def generate_remediation_plan(report: DependabotReport) -> dict[str, Any]:
    """Generate prioritized remediation plan."""
    categories = categorize_alerts(report.alerts)
    candidates = identify_auto_remediation_candidates(report.alerts)

    plan: dict[str, Any] = {
        "repository": report.repository,
        "generated_at": datetime.now(UTC).isoformat(),
        "priority_actions": [],
        "auto_remediation": {
            "eligible_count": len(candidates),
            "packages": [{"id": a.alert_id, "package": a.package_name} for a in candidates],
        },
    }

    for severity in ["critical", "high", "medium", "low"]:
        for alert in categories[severity]:
            plan["priority_actions"].append({
                "alert_id": alert.alert_id,
                "package": alert.package_name,
                "severity": severity,
                "action": "auto_pr" if alert in candidates else "manual_review",
                "patched_version": alert.patched_version,
            })

    return plan
