"""Agent 5: Exploratory Testing Assistant.

Guides testers toward high-risk areas using IPE-specific risk analysis,
defect history, and business critical path mapping.
"""

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from testing.ai.config import BUSINESS_CRITICAL_PATHS, SERVICE_REGISTRY, RiskLevel


PROMPT_TEMPLATE = """You are an experienced exploratory tester for manufacturing ERP platforms.

Using the following information about the IPE platform:

Business Critical Paths:
1. demand_to_schedule: dpe → mat → cap → fea → res (AI-driven priority → scheduling → resolution)
2. delay_to_copilot: del → nlp (delay detection → NLP classification → Copilot)
3. dsar_compliance: dpe (GDPR data subject access requests)
4. audit_immutability: dpe, cap, fea (cdm_audit_log REVOKE UPDATE/DELETE)
5. sop_financial_pipeline: dpe (S&OP forecast → solve → cost accounting → P&L)
6. digital_twin_disruption: network → alert (BOM explosion → supplier trace → war room)

Known Risk Areas:
- RLS bypass: Cross-tenant data access attempts
- JWT auth: Missing/expired tokens, wrong tenant
- Rate limiting: Kong 300/min per consumer threshold
- XAI compliance: contributing_factors must be float only
- Kafka event order: ipe.mo.material_scored must come BEFORE feasibility scoring
- Optimistic locking: res-svc approve with stale version → 409
- Audit log immutability: UPDATE/DELETE on cdm_audit_log must fail
- GDPR DSAR: 30-day completion requirement

Release notes:
{{release_notes}}

Historical defects:
{{defects}}

Create exploratory testing charters focused on:
- High-risk workflows (demand-to-schedule, DSAR compliance)
- Edge cases (empty DB, concurrent updates, network failures)
- Unusual user behavior (simultaneous MO approval, rate limit burst)
- Integration failures (Kafka event ordering, RLS context bleed)
- Data integrity risks (cross-tenant data, audit log tampering)

For each charter include:
- Mission statement
- Target area (service + feature)
- Suggested test ideas (5-10 specific scenarios)
- Exit criteria
- Risk justification (why this area needs exploratory testing)
"""


@dataclass
class ExploratoryCharter:
    charter_id: str
    mission: str
    target_service: str
    target_area: str
    test_ideas: list[str]
    exit_criteria: list[str]
    risk_justification: str
    risk_level: RiskLevel
    estimated_duration_minutes: int = 30


@dataclass
class ExploratorySession:
    session_id: str
    created_at: datetime
    charters: list[ExploratoryCharter]
    critical_path_charters: int = 0
    total_ideas: int = 0

    def __post_init__(self):
        self.critical_path_charters = sum(1 for c in self.charters if c.risk_level == RiskLevel.CRITICAL)
        self.total_ideas = sum(len(c.test_ideas) for c in self.charters)


IPE_RISK_AREAS = [
    {
        "area": "RLS Isolation",
        "services": ["dpe-svc", "mat-svc", "cap-svc", "fea-svc", "res-svc"],
        "risk": RiskLevel.CRITICAL,
        "ideas": [
            "Create data with tenant A, attempt read with tenant B JWT",
            "Direct SQL injection via SET app.current_tenant_id",
            "Bulk API with mixed tenant data in request body",
            "WebSocket connection with tenant A token subscribing to tenant B channel",
            "Concurrent requests rapidly switching tenant context",
        ],
    },
    {
        "area": "Kafka Event Ordering",
        "services": ["dpe-svc", "mat-svc", "fea-svc"],
        "risk": RiskLevel.CRITICAL,
        "ideas": [
            "Send ipe.mo.feasibility_scored BEFORE ipe.mo.material_scored",
            "Send same demand.classified event twice (test idempotency)",
            "Send event with invalid Avro schema",
            "Kill Kafka consumer mid-processing, verify DLQ",
            "Send events out of chronological order",
        ],
    },
    {
        "area": "Concurrent Operations",
        "services": ["res-svc", "cap-svc"],
        "risk": RiskLevel.HIGH,
        "ideas": [
            "Two planners approve same scenario simultaneously (test optimistic locking)",
            "Schedule same MO in two scenarios simultaneously",
            "DSAR subject requests access while tenant is being archived",
            "Rate limit burst: send 301 requests in 1 minute",
            "Update feasibility score while copilot is generating explanation",
        ],
    },
    {
        "area": "Data Integrity",
        "services": ["dpe-svc", "alert-svc"],
        "risk": RiskLevel.CRITICAL,
        "ideas": [
            "Attempt UPDATE on cdm_audit_log (should get permission denied)",
            "Attempt DELETE on cdm_audit_log (should get permission denied)",
            "Submit DSAR request, verify 30-day deadline tracking",
            "Request data export for tenant with 1M+ rows (test async handling)",
            "Submit GDPR erasure request, verify data is actually deleted",
        ],
    },
    {
        "area": "LLM/NLP Edge Cases",
        "services": ["nlp-svc", "del-svc"],
        "risk": RiskLevel.MEDIUM,
        "ideas": [
            "Send empty string query to copilot",
            "Send 10,000 character query to copilot",
            "Send query with PII (email, SSN, phone) - verify PII stripping",
            "Send query in non-English language",
            "Send query with special characters, SQL injection attempts",
            "Test tiered LLM routing with all 3 tiers",
            "Verify ON_PREM tier makes zero external network calls",
        ],
    },
    {
        "area": "Digital Twin Scale",
        "services": ["network-svc"],
        "risk": RiskLevel.MEDIUM,
        "ideas": [
            "BOM explosion with 10-level deep nesting (1000+ components)",
            "Supplier trace with 50+ downstream MOs affected",
            "Disruption simulation with cascading tier-2 → tier-1 impact",
            "Concurrent BOM explosions for same MO",
            "MO that doesn't exist in database",
        ],
    },
    {
        "area": "Financial Accuracy",
        "services": ["dpe-svc"],
        "risk": RiskLevel.HIGH,
        "ideas": [
            "COGM calculation with zero quantities (division by zero)",
            "COPQ with 100% scrap rate",
            "Variance analysis with matching planned/actual (zero variance)",
            "S&OP solver with 0 demand (edge case)",
            "Cost accounting with custom GL mapping override",
        ],
    },
]


class ExploratoryTestingAgent:

    def __init__(self, output_dir: str = "testing/ai/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_charters(
        self,
        release_scope: str = "full",
        focus_areas: list[str] | None = None,
        defect_history: dict[str, list[str]] | None = None,
    ) -> ExploratorySession:
        charters: list[ExploratoryCharter] = []
        defect_history = defect_history or {}

        for risk_area in IPE_RISK_AREAS:
            if focus_areas and risk_area["area"] not in focus_areas:
                continue

            relevant_defects = []
            for svc in risk_area["services"]:
                relevant_defects.extend(defect_history.get(svc, []))

            charter = ExploratoryCharter(
                charter_id=f"EXP-{risk_area['area'].replace(' ', '_')[:8].upper()}-{len(charters)+1:03d}",
                mission=f"Explore {risk_area['area']} scenarios across {', '.join(risk_area['services'][:3])} to find edge cases and integration failures",
                target_service=risk_area["services"][0],
                target_area=risk_area["area"],
                test_ideas=risk_area["ideas"],
                exit_criteria=[
                    f"All {len(risk_area['ideas'])} test ideas explored or documented as N/A",
                    f"No critical defects found in {risk_area['area']}",
                    f"RLS isolation verified for all affected services" if risk_area["area"] == "RLS Isolation" else "No new defect patterns discovered",
                ],
                risk_justification=f"{risk_area['risk'].value} risk area with {len(risk_area['ideas'])} test scenarios. Recent defects: {len(relevant_defects)}.",
                risk_level=risk_area["risk"],
                estimated_duration_minutes=max(15, len(risk_area["ideas"]) * 5),
            )
            charters.append(charter)

        for path in BUSINESS_CRITICAL_PATHS:
            charter = ExploratoryCharter(
                charter_id=f"EXP-{path['name'][:8].upper()}-{len(charters)+1:03d}",
                mission=f"End-to-end exploratory testing of {path['description']}",
                target_service=path["services"][0],
                target_area=path["name"],
                test_ideas=[
                    f"Walk through entire path: {' → '.join(path['services'])}",
                    "Introduce failure at each service boundary (network timeout, 500 error)",
                    "Test with malformed Kafka events at each consumer",
                    "Test with expired/missing auth at each service",
                    "Test with concurrent requests across multiple tenants",
                ],
                exit_criteria=[
                    f"Path {path['name']} works end-to-end with no data loss",
                    f"Each service boundary handles failures gracefully",
                ],
                risk_justification=f"Business critical path ({path['risk']} risk): {path['description']}",
                risk_level=RiskLevel(path["risk"]),
                estimated_duration_minutes=45,
            )
            charters.append(charter)

        return ExploratorySession(
            session_id=f"EXP-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}",
            created_at=datetime.now(UTC),
            charters=charters,
        )

    def export_to_json(self, session: ExploratorySession, filename: str = "exploratory_charters.json"):
        path = self.output_dir / filename
        data = {
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
            "total_charters": len(session.charters),
            "critical_path_charters": session.critical_path_charters,
            "total_ideas": session.total_ideas,
            "charters": [
                {
                    "charter_id": c.charter_id,
                    "mission": c.mission,
                    "target_service": c.target_service,
                    "target_area": c.target_area,
                    "test_ideas": c.test_ideas,
                    "exit_criteria": c.exit_criteria,
                    "risk_justification": c.risk_justification,
                    "risk_level": c.risk_level.value,
                    "estimated_duration_minutes": c.estimated_duration_minutes,
                }
                for c in session.charters
            ],
        }
        path.write_text(json.dumps(data, indent=2))
        return str(path)