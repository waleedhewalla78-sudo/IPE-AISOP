"""Agent 2: Regression Testing Agent.

Prioritizes and executes regression suites based on release scope,
dependency risk, and historical defect data.
"""

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from testing.ai.config import BUSINESS_CRITICAL_PATHS, SERVICE_REGISTRY, RiskLevel


@dataclass
class RegressionTest:
    test_id: str
    service: str
    endpoint: str
    method: str
    priority: str  # must_run / should_run / optional
    reason: str
    estimated_time_seconds: int = 5


@dataclass
class RegressionSuite:
    suite_id: str
    created_at: datetime
    release_scope: str
    must_run: list[RegressionTest]
    should_run: list[RegressionTest]
    optional: list[RegressionTest]
    total_estimated_time_seconds: int = 0
    critical_path_coverage: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.total_estimated_time_seconds = sum(
            t.estimated_time_seconds for t in self.must_run + self.should_run + self.optional
        )
        self.critical_path_coverage = list({
            t.service for t in self.must_run if t.priority == "must_run"
        })


PROMPT_TEMPLATE = """You are a release QA lead for the IPE manufacturing platform.

Analyze the following release changes and determine the minimum regression suite required.

IPE Service Dependency Map:
- dpe-svc depends on: PostgreSQL, Redis, Kafka, mat-svc, fea-svc
- mat-svc depends on: PostgreSQL, Redis, Kafka, dpe-svc
- cap-svc depends on: PostgreSQL, Redis, OR-Tools solver
- fea-svc depends on: PostgreSQL, Redis, Kafka, dpe-svc, mat-svc
- res-svc depends on: PostgreSQL, Redis
- del-svc depends on: PostgreSQL, Redis, Anthropic API
- nlp-svc depends on: Anthropic API, Redis, dpe-svc, mat-svc, cap-svc
- alert-svc depends on: PostgreSQL, Redis, Kafka

Critical Business Paths:
1. demand_to_schedule: dpe → mat → cap → fea → res
2. delay_to_copilot: del → nlp
3. dsar_compliance: dpe (GDPR endpoints)
4. audit_immutability: dpe, cap, fea

Release scope:
{{release_scope}}

Changed components:
{{changed_components}}

Historical defects (last 30 days):
{{defect_history}}

Prioritize tests based on:
- Customer impact (critical paths first)
- Dependency risk (changed services + downstream dependents)
- Failure history (services with recent defects)
- Business criticality (dpe, mat, cap, fea are critical)

Categorize each test as: must_run, should_run, or optional.
Provide justification for each recommendation.
"""


class RegressionAgent:

    def __init__(self, output_dir: str = "testing/ai/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def prioritize(
        self,
        changed_services: list[str],
        defect_history: dict[str, int] | None = None,
        release_scope: str = "patch",
    ) -> RegressionSuite:
        defect_history = defect_history or {}
        must_run: list[RegressionTest] = []
        should_run: list[RegressionTest] = []
        optional: list[RegressionTest] = []

        affected_services = set(changed_services)
        for service in changed_services:
            svc = SERVICE_REGISTRY.get(service)
            if svc:
                for path in BUSINESS_CRITICAL_PATHS:
                    if service in path["services"]:
                        for dep_service in path["services"]:
                            affected_services.add(dep_service)

        for service_name, svc_config in SERVICE_REGISTRY.items():
            svc_risk = svc_config.config.risk_level
            is_affected = service_name in affected_services
            has_defects = defect_history.get(service_name, 0) > 0
            is_critical = svc_config.config.business_critical

            if is_affected and (is_critical or has_defects):
                priority = "must_run"
            elif is_affected or is_critical:
                priority = "should_run"
            else:
                priority = "optional"

            test = RegressionTest(
                test_id=f"REG-{service_name[:3].upper()}-{len(must_run) + len(should_run) + len(optional) + 1:03d}",
                service=service_name,
                endpoint=svc_config.config.health_endpoint,
                method="GET",
                priority=priority,
                reason=self._reason(service_name, is_affected, is_critical, has_defects),
                estimated_time_seconds=max(5, int(svc_config.regression_weight * 10)),
            )

            if priority == "must_run":
                must_run.append(test)
            elif priority == "should_run":
                should_run.append(test)
            else:
                optional.append(test)

        for path in BUSINESS_CRITICAL_PATHS:
            test = RegressionTest(
                test_id=f"REG-E2E-{path['name'][:4].upper()}-{len(must_run):03d}",
                service="e2e",
                endpoint=path["description"],
                method="E2E",
                priority="must_run",
                reason=f"Critical business path: {path['name']} ({path['risk']} risk)",
                estimated_time_seconds=30,
            )
            must_run.append(test)

        suite = RegressionSuite(
            suite_id=f"REG-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}",
            created_at=datetime.now(UTC),
            release_scope=release_scope,
            must_run=must_run,
            should_run=should_run,
            optional=optional,
        )
        return suite

    def _reason(self, service: str, is_affected: bool, is_critical: bool, has_defects: bool) -> str:
        reasons = []
        if is_affected:
            reasons.append("service affected by changes")
        if is_critical:
            reasons.append("business-critical service")
        if has_defects:
            reasons.append("recent defect history")
        return "; ".join(reasons) if reasons else "routine regression"

    def export_to_json(self, suite: RegressionSuite, filename: str = "regression_suite.json"):
        path = self.output_dir / filename
        data = {
            "suite_id": suite.suite_id,
            "created_at": suite.created_at.isoformat(),
            "release_scope": suite.release_scope,
            "must_run_count": len(suite.must_run),
            "should_run_count": len(suite.should_run),
            "optional_count": len(suite.optional),
            "total_estimated_time_seconds": suite.total_estimated_time_seconds,
            "critical_path_coverage": suite.critical_path_coverage,
            "tests": {
                "must_run": [{"test_id": t.test_id, "service": t.service, "reason": t.reason} for t in suite.must_run],
                "should_run": [{"test_id": t.test_id, "service": t.service, "reason": t.reason} for t in suite.should_run],
                "optional": [{"test_id": t.test_id, "service": t.service, "reason": t.reason} for t in suite.optional],
            },
        }
        path.write_text(json.dumps(data, indent=2))
        return str(path)