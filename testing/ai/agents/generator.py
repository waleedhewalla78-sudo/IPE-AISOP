"""Agent 1: Test Generation Agent.

Generates test scenarios from requirements, API specs, and user stories.
Produces pytest-ready test cases with IPE-specific patterns.
"""

import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from testing.ai.config import (
    BUSINESS_CRITICAL_PATHS,
    AutomationSuitability,
    RiskLevel,
    SERVICE_REGISTRY,
    ServiceName,
)


class TestCategory(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    ERROR_HANDLING = "error_handling"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    RLS_ISOLATION = "rls_isolation"
    IDCEMPOTENCY = "idempotency"


@dataclass
class TestCase:
    test_id: str
    category: TestCategory
    service: str
    endpoint: str
    method: str
    preconditions: list[str]
    steps: list[str]
    expected_results: list[str]
    priority: RiskLevel
    automation_suitability: AutomationSuitability
    risk_level: RiskLevel
    business_path: str | None = None
    xai_constraint: str | None = None


@dataclass
class GenerationResult:
    test_cases: list[TestCase]
    coverage_gaps: list[str]
    suggestions: list[str]
    total_count: int = 0
    by_category: dict[str, int] = field(default_factory=dict)
    by_service: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        self.total_count = len(self.test_cases)
        self.by_category = {}
        self.by_service = {}
        for tc in self.test_cases:
            self.by_category[tc.category.value] = self.by_category.get(tc.category.value, 0) + 1
            self.by_service[tc.service] = self.by_service.get(tc.service, 0) + 1


PROMPT_TEMPLATE = """You are a senior QA engineer specializing in manufacturing ERP platforms.

Analyze the following requirements and generate comprehensive test scenarios for the IPE platform.

IPE Architecture Context:
- 14 microservices with FastAPI + SQLAlchemy + PostgreSQL
- Kong API Gateway with JWT auth and rate limiting
- RLS (Row-Level Security) for tenant isolation
- Kafka event mesh with Avro schemas
- OR-Tools CP-SAT solver for scheduling
- Monte Carlo ATP for material availability

Requirements:
{{requirements}}

IPE Constitution Constraints:
1. RLS: Every table with tenant_id must enforce tenant isolation
2. Auth: Every non-health endpoint must return 401 without valid JWT
3. Tests: Every service must have ≥80% unit test coverage
4. Event Mesh: Every state change must emit a Kafka event
5. Service Consistency: Every API must return {success, data, error}
6. Observability: Every service must expose /metrics and structured JSON logs

Generate test cases covering:
1. Positive: happy path for each endpoint
2. Negative: invalid inputs, missing auth, wrong tenant
3. Boundary: UUID edge cases, pagination limits, numeric thresholds
4. Error handling: 500 recovery, DLQ, timeout handling
5. Security: RLS bypass attempts, rate limiting, CORS
6. Performance: concurrent requests, large payloads, long-running queries
7. Compliance: GDPR DSAR, audit log immutability, data retention
8. RLS isolation: cross-tenant data access attempts

For each test case provide:
- Test ID (IPE-{service}-{category}-{NNN})
- Preconditions (DB seed, auth state, Kafka state)
- Test steps (HTTP requests with full URL, headers, body)
- Expected results (status code, response shape, DB state)
- Priority (critical/high/medium/low)
- Automation suitability (must_automate/should_automate/manual_only/exploratory)
- Risk level
- Which business critical path it covers (if any)
"""

IPE_SPECIFIC_PATTERNS = {
    "auth_headers": {
        "valid": {"Authorization": "Bearer {jwt_token}", "X-Tenant-ID": "{tenant_id}"},
        "missing_auth": {"X-Tenant-ID": "{tenant_id}"},
        "missing_tenant": {"Authorization": "Bearer {jwt_token}"},
        "wrong_tenant": {"Authorization": "Bearer {jwt_token}", "X-Tenant-ID": "{different_tenant_id}"},
        "expired_jwt": {"Authorization": "Bearer {expired_jwt}", "X-Tenant-ID": "{tenant_id}"},
    },
    "xai_validation": {
        "contributing_factors_must_be_float": True,
        "confidence_score_range": (0.0, 1.0),
        "constraints_must_be_list": True,
        "assumptions_must_be_list": True,
    },
    "response_shape": {
        "success": {"success": True, "data": {}, "error": None},
        "failure": {"success": False, "data": None, "error": {"code": "str", "message": "str"}},
    },
    "rls_test_tenants": {
        "tenant_a": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        "tenant_b": "b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22",
    },
}


class TestGenerationAgent:

    def __init__(self, output_dir: str = "testing/ai/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_from_endpoint(
        self,
        service: str,
        endpoint: str,
        method: str,
        risk_level: RiskLevel = RiskLevel.MEDIUM,
    ) -> list[TestCase]:
        cases = []
        svc = SERVICE_REGISTRY.get(service)
        base = svc.config.base_url if svc else "http://localhost:8000"

        for category in TestCategory:
            tc = TestCase(
                test_id=f"IPE-{service[:3].upper()}-{category.value[:4].upper()}-{len(cases)+1:03d}",
                category=category,
                service=service,
                endpoint=endpoint,
                method=method,
                preconditions=self._preconditions(category, service),
                steps=self._steps(category, base, endpoint, method),
                expected_results=self._expected(category),
                priority=risk_level,
                automation_suitability=self._automation_fit(category),
                risk_level=risk_level,
            )
            cases.append(tc)

        return cases

    def generate_from_requirements(self, requirements: str) -> GenerationResult:
        all_cases: list[TestCase] = []

        for path in BUSINESS_CRITICAL_PATHS:
            for service in path["services"]:
                svc = SERVICE_REGISTRY.get(service)
                if not svc:
                    continue
                for endpoint in svc.config.api_endpoints or ["/api/v1/health"]:
                    cases = self.generate_from_endpoint(
                        service=service,
                        endpoint=endpoint,
                        method="GET" if endpoint.startswith("/api/v1/health") else "POST",
                        risk_level=RiskLevel(path["risk"]),
                    )
                    for tc in cases:
                        tc.business_path = path["name"]
                    all_cases.extend(cases)

        for service, svc_config in SERVICE_REGISTRY.items():
            existing = [tc for tc in all_cases if tc.service == service]
            if not existing:
                cases = self.generate_from_endpoint(
                    service=service,
                    endpoint=svc_config.config.health_endpoint,
                    method="GET",
                    risk_level=svc_config.config.risk_level,
                )
                all_cases.extend(cases)

        coverage_gaps = self._find_coverage_gaps(all_cases)
        suggestions = self._generate_suggestions(all_cases, requirements)

        return GenerationResult(
            test_cases=all_cases,
            coverage_gaps=coverage_gaps,
            suggestions=suggestions,
        )

    def generate_rls_tests(self) -> list[TestCase]:
        cases = []
        tenant_a = IPE_SPECIFIC_PATTERNS["rls_test_tenants"]["tenant_a"]
        tenant_b = IPE_SPECIFIC_PATTERNS["rls_test_tenants"]["tenant_b"]

        for service, svc_config in SERVICE_REGISTRY.items():
            if not svc_config.has_database:
                continue
            tc = TestCase(
                test_id=f"IPE-{service[:3].upper()}-RLSX-{len(cases)+1:03d}",
                category=TestCategory.RLS_ISOLATION,
                service=service,
                endpoint="/api/v1/health",
                method="GET",
                preconditions=[
                    f"Seed data for tenant A ({tenant_a})",
                    f"Seed data for tenant B ({tenant_b})",
                    "Valid JWT for tenant A",
                ],
                steps=[
                    f"Authenticate as tenant A ({tenant_a})",
                    f"Request data belonging to tenant B ({tenant_b})",
                    "Verify response contains only tenant A data",
                    "Attempt direct SQL injection: SET app.current_tenant_id = invalid",
                    "Verify all queries respect RLS policies",
                ],
                expected_results=[
                    "Tenant A cannot see tenant B data",
                    "Direct RLS bypass attempts return 403 or empty results",
                    "All 48 tables with tenant_id enforce isolation",
                ],
                priority=RiskLevel.CRITICAL,
                automation_suitability=AutomationSuitability.MUST_AUTOMATE,
                risk_level=RiskLevel.CRITICAL,
                business_path="rls_isolation",
            )
            cases.append(tc)
        return cases

    def generate_xai_tests(self) -> list[TestCase]:
        cases = []
        xai_services = [
            (ServiceName.DPE, "/api/v1/demand/classify", "POST"),
            (ServiceName.MAT, "/api/v1/material/probabilistic-atp", "POST"),
            (ServiceName.CAP, "/api/v1/capacity/schedule", "POST"),
            (ServiceName.FEA, "/api/v1/feasibility/score", "POST"),
        ]

        for service, endpoint, method in xai_services:
            cases.append(TestCase(
                test_id=f"IPE-{service[:3].upper()}-XAIX-{len(cases)+1:03d}",
                category=TestCategory.COMPLIANCE,
                service=service,
                endpoint=endpoint,
                method=method,
                preconditions=["Valid JWT", "Seed data with known priority scores"],
                steps=[
                    f"POST {endpoint} with valid data",
                    "Check response contains xai_explanation field",
                    "Verify contributing_factors contains only float values",
                    "Verify confidence_score is between 0.0 and 1.0",
                    "Verify constraints is a list of strings",
                    "Verify assumptions is a list of strings",
                ],
                expected_results=[
                    "xai_explanation.contributing_factors values are all float",
                    "xai_explanation.confidence_score in [0.0, 1.0]",
                    "No string values in contributing_factors dict",
                ],
                priority=RiskLevel.CRITICAL,
                automation_suitability=AutomationSuitability.MUST_AUTOMATE,
                risk_level=RiskLevel.CRITICAL,
            ))
        return cases

    def _preconditions(self, category: TestCategory, service: str) -> list[str]:
        base = ["Service is running and healthy", "Database is seeded with test data"]
        if category in (TestCategory.SECURITY, TestCategory.RLS_ISOLATION):
            base.extend(["Valid JWT for tenant A", "Valid JWT for tenant B (different tenant)"])
        if category == TestCategory.ERROR_HANDLING:
            base.append("Kafka broker may be unavailable")
        if category == TestCategory.PERFORMANCE:
            base.append(" ausreichend test data for load (>1000 records)")
        return base

    def _steps(self, category: TestCategory, base_url: str, endpoint: str, method: str) -> list[str]:
        if category == TestCategory.POSITIVE:
            return [f"{method} {base_url}{endpoint} with valid data and auth headers"]
        elif category == TestCategory.NEGATIVE:
            return [
                f"{method} {base_url}{endpoint} without auth headers → expect 401",
                f"{method} {base_url}{endpoint} with invalid UUID → expect 422",
                f"{method} {base_url}{endpoint} with wrong tenant → expect 403/empty",
            ]
        elif category == TestCategory.BOUNDARY:
            return [
                f"{method} {base_url}{endpoint} with empty list → expect 200/422",
                f"{method} {base_url}{endpoint} with max-length strings → expect 200/422",
            ]
        elif category == TestCategory.SECURITY:
            return [
                f"{method} {base_url}{endpoint} with tenant A JWT querying tenant B data → expect 403/empty",
                f"{method} {base_url}{endpoint} with expired JWT → expect 401",
                f"{method} {base_url}{endpoint} with rate limit exceeded → expect 429",
            ]
        elif category == TestCategory.COMPLIANCE:
            return [f"{method} {base_url}{endpoint} → verify XAI payload compliance"]
        return [f"{method} {base_url}{endpoint}"]

    def _expected(self, category: TestCategory) -> list[str]:
        if category == TestCategory.XAIConstraint:
            return ["Response follows IPE standard shape: {success, data, error}"]
        if category in (TestCategory.SECURITY, TestCategory.RLS_ISOLATION):
            return ["Cross-tenant data is inaccessible", "Rate limiting enforced"]
        return ["Response follows IPE standard shape: {success, data, error}"]

    def _automation_fit(self, category: TestCategory) -> AutomationSuitability:
        if category in (TestCategory.POSITIVE, TestCategory.NEGATIVE, TestCategory.BOUNDARY, TestCategory.RLS_ISOLATION):
            return AutomationSuitability.MUST_AUTOMATE
        if category in (TestCategory.ERROR_HANDLING, TestCategory.COMPLIANCE):
            return AutomationSuitability.SHOULD_AUTOMATE
        if category == TestCategory.PERFORMANCE:
            return AutomationSuitability.SHOULD_AUTOMATE
        return AutomationSuitability.EXPLORATORY

    def _find_coverage_gaps(self, cases: list[TestCase]) -> list[str]:
        covered_services = {tc.service for tc in cases}
        covered_categories = {tc.category for tc in cases}
        gaps = []

        for service in SERVICE_REGISTRY:
            if service not in covered_services:
                gaps.append(f"No tests for {service}")

        for cat in TestCategory:
            if cat not in covered_categories:
                gaps.append(f"No {cat.value} tests generated")

        return gaps

    def _generate_suggestions(self, cases: list[TestCase], requirements: str) -> list[str]:
        suggestions = []
        must_auto = [tc for tc in cases if tc.automation_suitability == AutomationSuitability.MUST_AUTOMATE]
        if len(must_auto) < 20:
            suggestions.append("Consider adding more positive/negative test cases for full automation coverage")
        critical = [tc for tc in cases if tc.priority == RiskLevel.CRITICAL]
        if len(critical) < 10:
            suggestions.append("Need more critical-priority tests for business-critical paths")
        rls = [tc for tc in cases if tc.category == TestCategory.RLS_ISOLATION]
        if len(rls) < len([s for s in SERVICE_REGISTRY.values() if s.has_database]):
            suggestions.append("RLS isolation tests should cover every service with database access")
        return suggestions

    def export_to_json(self, result: GenerationResult, filename: str = "generated_tests.json"):
        path = self.output_dir / filename
        data = {
            "total_count": result.total_count,
            "by_category": result.by_category,
            "by_service": result.by_service,
            "coverage_gaps": result.coverage_gaps,
            "suggestions": result.suggestions,
            "test_cases": [
                {
                    "test_id": tc.test_id,
                    "category": tc.category.value,
                    "service": tc.service,
                    "endpoint": tc.endpoint,
                    "method": tc.method,
                    "priority": tc.priority.value,
                    "automation_suitability": tc.automation_suitability.value,
                    "risk_level": tc.risk_level.value,
                    "business_path": tc.business_path,
                    "preconditions": tc.preconditions,
                    "steps": tc.steps,
                    "expected_results": tc.expected_results,
                }
                for tc in result.test_cases
            ],
        }
        path.write_text(json.dumps(data, indent=2))
        return str(path)