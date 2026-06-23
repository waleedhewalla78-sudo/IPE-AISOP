"""Agent 6: Test Optimization Agent.

Reduces execution time while maintaining coverage by analyzing
test execution history, coverage data, and code changes.
"""

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from testing.ai.config import SERVICE_REGISTRY


PROMPT_TEMPLATE = """You are a QA optimization specialist for the IPE manufacturing platform.

Current test suite:
- 897 Python unit tests across 15 service test suites
- 74 integration tests (8 skip without infrastructure)
- 17 frontend tests
- k6 load tests (0% failure, p95 < 50ms)
- Schemathesis contract tests (config created, not in CI)

Test execution history:
{{execution_history}}

Coverage data:
{{coverage}}

Recent code changes:
{{changes}}

Service risk matrix:
- CRITICAL: dpe-svc, mat-svc, cap-svc, fea-svc (business-critical paths)
- HIGH: res-svc, connector, scn-svc
- MEDIUM: del-svc, nlp-svc, alert-svc, quality-svc, network-svc
- LOW: rec-svc, sustain-svc, ml-svc

Recommend:
1. Tests to remove (redundant or testing implementation details)
2. Tests to merge (similar scenarios across services)
3. Redundant scenarios (same assertion tested multiple times)
4. Coverage gaps (untested code paths, especially in RLS and auth)
5. Execution priorities (must-run vs. can-skip for PR builds)

Optimize for maximum risk coverage with minimum execution time.
Target: PR build < 10 min, Full build < 30 min, Nightly < 60 min.
"""


@dataclass
class TestRecommendation:
    test_id: str
    service: str
    action: str  # keep, remove, merge, skip_for_pr
    reason: str
    risk_impact: str  # none, low, medium, high
    estimated_time_saved_seconds: int = 0
    merged_with: list[str] | None = None


@dataclass
class OptimizationResult:
    total_tests: int
    keep: int
    remove: int
    merge: int
    skip_for_pr: int
    recommendations: list[TestRecommendation]
    coverage_gaps: list[str]
    pr_build_time_estimate_seconds: int = 0
    full_build_time_estimate_seconds: int = 0
    nightly_build_time_estimate_seconds: int = 0


IPE_TEST_PATTERNS = {
    "redundant_health_checks": {
        "description": "Every service has a health check test that just asserts status == 200",
        "action": "merge",
        "savings_per_test_seconds": 2,
        "risk": "low",
    },
    "duplicate_uuid_validation": {
        "description": "Multiple services test the same UUID validation patterns",
        "action": "consolidate",
        "savings_per_test_seconds": 3,
        "risk": "low",
    },
    "overlapping_priority_scoring": {
        "description": "dpe-svc has multiple tests for priority scoring with different inputs",
        "action": "merge",
        "savings_per_test_seconds": 5,
        "risk": "medium",
    },
    "identical_kafka_consumer_tests": {
        "description": "Each service's consumer tests follow the same pattern",
        "action": "parameterize",
        "savings_per_test_seconds": 3,
        "risk": "medium",
    },
}


class TestOptimizationAgent:

    def __init__(self, output_dir: str = "testing/ai/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def analyze(
        self,
        test_counts: dict[str, int] | None = None,
        execution_times: dict[str, float] | None = None,
        changed_services: list[str] | None = None,
    ) -> OptimizationResult:
        test_counts = test_counts or {s: svc.config.risk_level for s, svc in SERVICE_REGISTRY.items()}
        execution_times = execution_times or {}
        changed_services = changed_services or []

        recommendations: list[TestRecommendation] = []
        total_tests = 0
        keep_count = 0
        remove_count = 0
        merge_count = 0
        skip_for_pr_count = 0
        total_time_saved = 0

        for service, svc_config in SERVICE_REGISTRY.items():
            is_critical = svc_config.config.business_critical
            is_changed = service in changed_services
            risk = svc_config.config.risk_level
            test_time = execution_times.get(service, 10.0)

            total_tests += 1

            if risk == RiskLevel.CRITICAL or is_changed:
                recommendations.append(TestRecommendation(
                    test_id=f"OPT-{service[:3].upper()}-001",
                    service=service,
                    action="keep",
                    reason=f"{'Business-critical service' if is_critical else 'Changed in this release'}",
                    risk_impact="none",
                    estimated_time_saved_seconds=0,
                ))
                keep_count += 1
            elif risk == RiskLevel.MEDIUM:
                recommendations.append(TestRecommendation(
                    test_id=f"OPT-{service[:3].upper()}-002",
                    service=service,
                    action="skip_for_pr",
                    reason="Medium-risk service, not changed in this release",
                    risk_impact="low",
                    estimated_time_saved_seconds=int(test_time),
                ))
                skip_for_pr_count += 1
                total_time_saved += int(test_time)
            elif risk == RiskLevel.LOW:
                recommendations.append(TestRecommendation(
                    test_id=f"OPT-{service[:3].upper()}-003",
                    service=service,
                    action="skip_for_pr",
                    reason="Low-risk service, only run in nightly builds",
                    risk_impact="low",
                    estimated_time_saved_seconds=int(test_time),
                ))
                skip_for_pr_count += 1
                total_time_saved += int(test_time)

        for pattern_name, pattern in IPE_TEST_PATTERNS.items():
            recommendations.append(TestRecommendation(
                test_id=f"OPT-PATTERN-{pattern_name[:8].upper()}",
                service="all",
                action=pattern["action"],
                reason=pattern["description"],
                risk_impact=pattern["risk"],
                estimated_time_saved_seconds=pattern["savings_per_test_seconds"],
            ))
            merge_count += 1

        coverage_gaps = self._find_coverage_gaps()

        pr_time = sum(execution_times.get(s, 10.0) for s in changed_services) if changed_services else 120
        full_time = sum(execution_times.values()) if execution_times else 600
        nightly_time = full_time + 300  # integration + E2E + k6

        return OptimizationResult(
            total_tests=total_tests,
            keep=keep_count,
            remove=remove_count,
            merge=merge_count,
            skip_for_pr=skip_for_pr_count,
            recommendations=recommendations,
            coverage_gaps=coverage_gaps,
            pr_build_time_estimate_seconds=int(pr_time),
            full_build_time_estimate_seconds=int(full_time),
            nightly_build_time_estimate_seconds=int(nightly_time),
        )

    def _find_coverage_gaps(self) -> list[str]:
        gaps = [
            "RLS isolation: No automated test verifying cross-tenant data access returns empty",
            "Kafka event ordering: No test verifying ipe.mo.material_scored arrives before feasibility_scored",
            "GDPR DSAR: No test verifying 30-day deadline enforcement",
            "Audit log immutability: No test verifying REVOKE UPDATE/DELETE on cdm_audit_log",
            "Rate limiting: No automated test verifying 429 at 301st request/min",
            "XAI compliance: No automated test verifying contributing_factors are all float",
            "PII stripping: No test verifying PII is redacted in copilot queries",
            "Tiered LLM routing: No test verifying ON_PREM tier makes no external calls",
            "Data retention: No test verifying TTL enforcement on cdm_audit_log",
            "JWT JWKS: No test verifying JWKS validation works with RS256 tokens",
        ]
        return gaps

    def export_to_json(self, result: OptimizationResult, filename: str = "optimization_result.json"):
        path = self.output_dir / filename
        data = {
            "total_tests": result.total_tests,
            "keep": result.keep,
            "remove": result.remove,
            "merge": result.merge,
            "skip_for_pr": result.skip_for_pr,
            "pr_build_time_estimate_seconds": result.pr_build_time_estimate_seconds,
            "full_build_time_estimate_seconds": result.full_build_time_estimate_seconds,
            "nightly_build_time_estimate_seconds": result.nightly_build_time_estimate_seconds,
            "coverage_gaps": result.coverage_gaps,
            "recommendations": [
                {
                    "test_id": r.test_id,
                    "service": r.service,
                    "action": r.action,
                    "reason": r.reason,
                    "risk_impact": r.risk_impact,
                    "estimated_time_saved_seconds": r.estimated_time_saved_seconds,
                    "merged_with": r.merged_with,
                }
                for r in result.recommendations
            ],
        }
        path.write_text(json.dumps(data, indent=2))
        return str(path)


from testing.ai.config import RiskLevel