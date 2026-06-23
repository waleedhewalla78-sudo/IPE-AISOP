"""Bandit SAST integration for IPE.

Wraps bandit as a library for programmatic security scanning.
Generates structured findings with severity, confidence, and remediation guidance.
"""
from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("ipe.security.sast")


@dataclass
class BanditFinding:
    filename: str
    line_number: int
    issue_text: str
    issue_cwe: dict[str, Any]
    issue_severity: str
    issue_confidence: str
    code: str

    @property
    def severity_score(self) -> int:
        return {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(self.issue_severity, 0)

    @property
    def confidence_score(self) -> int:
        return {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(self.issue_confidence, 0)

    @property
    def risk_score(self) -> int:
        return self.severity_score * self.confidence_score


@dataclass
class SastReport:
    scan_target: str
    total_files_scanned: int = 0
    total_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    findings: list[BanditFinding] = field(default_factory=list)
    scan_duration_seconds: float = 0.0

    @property
    def risk_summary(self) -> dict[str, int]:
        return {
            "HIGH": self.high_findings,
            "MEDIUM": self.medium_findings,
            "LOW": self.low_findings,
        }


def run_bandit_scan(
    target_path: str,
    severity_threshold: str = "LOW",
    confidence_threshold: str = "LOW",
    excluded_paths: list[str] | None = None,
) -> SastReport:
    """Run bandit scan and return structured report."""
    args = [
        "bandit",
        "-r", target_path,
        "-f", "json",
        "--severity-level", severity_threshold,
        "--confidence-level", confidence_threshold,
    ]
    if excluded_paths:
        for p in excluded_paths:
            args.extend(["--exclude", p])

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=300,
        )
        data = json.loads(result.stdout) if result.stdout else {}
    except subprocess.TimeoutExpired:
        logger.error("Bandit scan timed out for %s", target_path)
        return SastReport(scan_target=target_path)
    except (json.JSONDecodeError, FileNotFoundError) as exc:
        logger.error("Bandit scan failed: %s", exc)
        return SastReport(scan_target=target_path)

    findings: list[BanditFinding] = []
    for item in data.get("results", []):
        findings.append(BanditFinding(
            filename=item.get("filename", ""),
            line_number=item.get("line_number", 0),
            issue_text=item.get("issue_text", ""),
            issue_cwe=item.get("issue_cwe", {}),
            issue_severity=item.get("issue_severity", "LOW"),
            issue_confidence=item.get("issue_confidence", "LOW"),
            code=item.get("code", ""),
        ))

    return SastReport(
        scan_target=target_path,
        total_files_scanned=data.get("metrics", {}).get("_totals", {}).get("loc", 0),
        total_findings=len(findings),
        high_findings=sum(1 for f in findings if f.issue_severity == "HIGH"),
        medium_findings=sum(1 for f in findings if f.issue_severity == "MEDIUM"),
        low_findings=sum(1 for f in findings if f.issue_severity == "LOW"),
        findings=findings,
    )


def generate_sarif(report: SastReport) -> dict[str, Any]:
    """Convert SAST report to SARIF format for GitHub integration."""
    rules: dict[str, dict[str, Any]] = {}
    results = []

    for finding in report.findings:
        cwe_id = finding.issue_cwe.get("id", "CWE-0")
        rule_id = cwe_id.split("-")[-1] if cwe_id.startswith("CWE-") else "unknown"

        if rule_id not in rules:
            rules[rule_id] = {
                "id": rule_id,
                "shortDescription": {"text": finding.issue_text},
                "defaultConfiguration": {"level": finding.issue_severity.lower()},
                "properties": {"tags": [f"security.{cwe_id}"]},
            }

        results.append({
            "ruleId": rule_id,
            "message": {"text": finding.issue_text},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": finding.filename},
                    "region": {"startLine": finding.line_number},
                }
            }],
        })

    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "bandit", "rules": list(rules.values())}},
            "results": results,
        }],
    }


_IPE_SECURITY_EXCLUSIONS = [
    "*/tests/*",
    "*/test_*",
    "*/conftest.py",
    "*/migrations/*",
]


def scan_ipe_services(services_root: str = "services") -> dict[str, SastReport]:
    """Scan all IPE services and return per-service reports."""
    reports: dict[str, SastReport] = {}
    services_path = Path(services_root)

    if not services_path.exists():
        logger.warning("Services root not found: %s", services_root)
        return reports

    for service_dir in services_path.iterdir():
        if service_dir.is_dir() and (service_dir / "app").exists():
            target = str(service_dir / "app")
            reports[service_dir.name] = run_bandit_scan(
                target_path=target,
                excluded_paths=_IPE_SECURITY_EXCLUSIONS,
            )
            logger.info(
                "SAST scan complete for %s: %d findings (%d high)",
                service_dir.name,
                reports[service_dir.name].total_findings,
                reports[service_dir.name].high_findings,
            )

    return reports
