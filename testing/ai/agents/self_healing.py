"""Agent 3: Self-Healing Automation Agent.

Reduces test maintenance by detecting and repairing broken selectors,
API endpoint changes, and response shape drift in IPE tests.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from testing.ai.config import SERVICE_REGISTRY


PROMPT_TEMPLATE = """You are an automation architect for the IPE manufacturing platform.

Analyze the failed test execution and recommend repairs.

IPE test infrastructure:
- Backend tests use httpx.AsyncClient with ASGITransport
- Auth uses JWT via create_access_token(USER_ID, TENANT_ID, role)
- Tenant isolation uses X-Tenant-ID header
- Response shape: {success: bool, data: dict, error: {code: str, message: str} | None}
- XAI explanation: {constraints: list, assumptions: list, confidence_score: float, contributing_factors: dict[str, float]}

Original selector/endpoint:
{{selector}}

Current DOM/API response:
{{current_state}}

Failure logs:
{{logs}}

Screenshots/error details:
{{error_details}}

Determine:
1. Root cause (selector change, API change, auth change, data change)
2. Recommended fix (updated selector, new endpoint, auth header change)
3. Confidence level (high/medium/low)
4. Potential side effects of the fix
5. Whether human approval is required

CRITICAL: Do not auto-approve changes affecting:
- Authentication flow
- RLS/tenant isolation
- Audit logging
- Financial calculations
"""


@dataclass
class SelectorFix:
    original: str
    proposed: str
    root_cause: str
    confidence: str  # high/medium/low
    side_effects: list[str]
    requires_human_approval: bool
    service: str
    test_file: str


@dataclass
class APIFix:
    original_endpoint: str
    new_endpoint: str
    original_shape: dict
    new_shape: dict
    changed_fields: list[str]
    requires_human_approval: bool
    service: str


@dataclass
class HealingResult:
    fixes: list[SelectorFix | APIFix]
    auto_applicable: int = 0
    requires_review: int = 0
    summary: str = ""

    def __post_init__(self):
        self.auto_applicable = sum(1 for f in self.fixes if not f.requires_human_approval)
        self.requires_review = sum(1 for f in self.fixes if f.requires_human_approval)
        self.summary = f"{self.auto_applicable} auto-fixable, {self.requires_review} require human review"


IPE_RESPONSE_SHAPE = {
    "success": {"type": "bool", "required": True},
    "data": {"type": "any", "required": True, "nullable": True},
    "error": {"type": "dict", "required": True, "nullable": True, "shape": {"code": "str", "message": "str"}},
}

IPE_AUTH_PATTERNS = {
    "valid_headers": ["Authorization", "X-Tenant-ID"],
    "expired_jwt_pattern": r"Bear?er\s+\S+\.\S+\.\S+",
    "missing_auth_codes": [401, 403],
}


class SelfHealingAgent:

    def __init__(self, output_dir: str = "testing/ai/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def analyze_failure(
        self,
        test_file: str,
        service: str,
        error_log: str,
        response_diff: dict | None = None,
    ) -> HealingResult:
        fixes: list[SelectorFix | APIFix] = []

        endpoint_patterns = [
            (r"/api/v1/(\w+)/(\w+)", "standard IPE endpoint pattern"),
            (r"status_code\s*==\s*(\d+)", "expected status code"),
            (r'json\(\)\["(\w+)"\]', "response field access"),
            (r'\.get\("(\w+)"\)', "dict field access"),
        ]

        auth_failures = re.findall(r"(40[13]|Unauthorized|Forbidden|No tenant)", error_log, re.IGNORECASE)
        if auth_failures:
            fixes.append(SelectorFix(
                original="auth_headers",
                proposed="Regenerate JWT with create_access_token() and verify X-Tenant-ID header",
                root_cause="Authentication failure - JWT expired or tenant header missing",
                confidence="high",
                side_effects=["May need to update JWT_SECRET_KEY if rotated"],
                requires_human_approval=False,
                service=service,
                test_file=test_file,
            ))

        uuid_failures = re.findall(r"(422|validation error|invalid UUID|invalid type)", error_log, re.IGNORECASE)
        if uuid_failures:
            fixes.append(SelectorFix(
                original="UUID parameter",
                proposed="Replace with valid UUID: str(uuid.uuid4())",
                root_cause="Invalid UUID format in request parameter",
                confidence="high",
                side_effects=[],
                requires_human_approval=False,
                service=service,
                test_file=test_file,
            ))

        if response_diff:
            for field, change in response_diff.items():
                if field == "contributing_factors":
                    fixes.append(APIFix(
                        original_endpoint=f"response.{field}",
                        new_endpoint=f"response.{field}",
                        original_shape={"type": "dict[str, float]"},
                        new_shape=change.get("new_type", {"type": "unknown"}),
                        changed_fields=[field],
                        requires_human_approval=True,
                        service=service,
                    ))
                elif field in ("success", "data", "error"):
                    fixes.append(APIFix(
                        original_endpoint=f"response.{field}",
                        new_endpoint=f"response.{field}",
                        original_shape={"type": IPE_RESPONSE_SHAPE[field]["type"]},
                        new_shape=change.get("new_type", {"type": "unknown"}),
                        changed_fields=[field],
                        requires_human_approval=True,
                        service=service,
                    ))

        return HealingResult(fixes=fixes)

    def check_response_shape(self, service: str, endpoint: str, response: dict) -> list[str]:
        violations = []
        if "success" not in response:
            violations.append(f"{service}{endpoint}: Missing 'success' field")
        if "data" not in response:
            violations.append(f"{service}{endpoint}: Missing 'data' field")
        if "error" not in response:
            violations.append(f"{service}{endpoint}: Missing 'error' field")

        if "xai_explanation" in str(response.get("data", {})):
            data = response.get("data", {})
            if isinstance(data, dict) and "xai_explanation" in data:
                xai = data["xai_explanation"]
                if "contributing_factors" in xai:
                    for key, val in xai["contributing_factors"].items():
                        if not isinstance(val, float):
                            violations.append(
                                f"{service}{endpoint}: XAI contributing_factors['{key}'] = {val} ({type(val).__name__}), expected float"
                            )
                if "confidence_score" in xai:
                    if not isinstance(xai["confidence_score"], float) or not (0.0 <= xai["confidence_score"] <= 1.0):
                        violations.append(
                            f"{service}{endpoint}: XAI confidence_score = {xai['confidence_score']}, expected float in [0.0, 1.0]"
                        )
        return violations