"""IPE Testing Framework Configuration.

Maps services, endpoints, risk levels, and test infrastructure settings.
"""

from dataclasses import dataclass, field
from enum import StrEnum


class ServiceName(StrEnum):
    DPE = "dpe-svc"
    MAT = "mat-svc"
    CAP = "cap-svc"
    FEA = "fea-svc"
    RES = "res-svc"
    DEL = "del-svc"
    NLP = "nlp-svc"
    REC = "rec-svc"
    ALERT = "alert-svc"
    CONNECTOR = "connector"
    SUSTAIN = "sustain-svc"
    QUALITY = "quality-svc"
    SCN = "scn-svc"
    NETWORK = "network-svc"
    ML = "ml-svc"


class RiskLevel(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AutomationSuitability(StrEnum):
    MUST_AUTOMATE = "must_automate"
    SHOULD_AUTOMATE = "should_automate"
    MANUAL_ONLY = "manual_only"
    EXPLORATORY = "exploratory"


@dataclass
class ServiceConfig:
    name: str
    port: int
    base_url: str
    health_endpoint: str = "/api/v1/health"
    risk_level: RiskLevel = RiskLevel.MEDIUM
    business_critical: bool = False
    api_endpoints: list[str] = field(default_factory=list)


@dataclass
class IPTEService:
    """Full service definition with risk and automation metadata."""
    config: ServiceConfig
    has_database: bool = True
    has_kafka_consumer: bool = False
    has_websocket: bool = False
    has_external_api: bool = False
    regression_weight: float = 1.0
    max_response_time_ms: int = 2000
    p95_threshold_ms: int = 500


SERVICE_REGISTRY: dict[str, IPTEService] = {
    ServiceName.DPE: IPTEService(
        config=ServiceConfig(
            name="dpe-svc", port=8020, base_url="http://localhost:8020",
            risk_level=RiskLevel.CRITICAL, business_critical=True,
        ),
        has_kafka_consumer=True, regression_weight=1.5,
    ),
    ServiceName.MAT: IPTEService(
        config=ServiceConfig(
            name="mat-svc", port=8002, base_url="http://localhost:8002",
            risk_level=RiskLevel.CRITICAL, business_critical=True,
        ),
        has_kafka_consumer=True, regression_weight=1.5,
    ),
    ServiceName.CAP: IPTEService(
        config=ServiceConfig(
            name="cap-svc", port=8003, base_url="http://localhost:8003",
            risk_level=RiskLevel.CRITICAL, business_critical=True,
        ),
        regression_weight=1.5,
    ),
    ServiceName.FEA: IPTEService(
        config=ServiceConfig(
            name="fea-svc", port=8004, base_url="http://localhost:8004",
            risk_level=RiskLevel.CRITICAL, business_critical=True,
        ),
        has_kafka_consumer=True, has_websocket=True, regression_weight=1.5,
    ),
    ServiceName.RES: IPTEService(
        config=ServiceConfig(
            name="res-svc", port=8005, base_url="http://localhost:8005",
            risk_level=RiskLevel.HIGH,
        ),
        regression_weight=1.2,
    ),
    ServiceName.DEL: IPTEService(
        config=ServiceConfig(
            name="del-svc", port=8006, base_url="http://localhost:8006",
            risk_level=RiskLevel.MEDIUM,
        ),
        has_kafka_consumer=True, has_external_api=True,
    ),
    ServiceName.NLP: IPTEService(
        config=ServiceConfig(
            name="nlp-svc", port=8007, base_url="http://localhost:8007",
            risk_level=RiskLevel.MEDIUM,
        ),
        has_external_api=True,
    ),
    ServiceName.REC: IPTEService(
        config=ServiceConfig(
            name="rec-svc", port=8008, base_url="http://localhost:8008",
            risk_level=RiskLevel.LOW,
        ),
    ),
    ServiceName.ALERT: IPTEService(
        config=ServiceConfig(
            name="alert-svc", port=8010, base_url="http://localhost:8010",
            risk_level=RiskLevel.MEDIUM,
        ),
        has_kafka_consumer=True,
    ),
    ServiceName.CONNECTOR: IPTEService(
        config=ServiceConfig(
            name="connector", port=8011, base_url="http://localhost:8011",
            risk_level=RiskLevel.HIGH,
        ),
    ),
    ServiceName.SUSTAIN: IPTEService(
        config=ServiceConfig(
            name="sustain-svc", port=8012, base_url="http://localhost:8012",
            risk_level=RiskLevel.LOW,
        ),
    ),
    ServiceName.QUALITY: IPTEService(
        config=ServiceConfig(
            name="quality-svc", port=8013, base_url="http://localhost:8013",
            risk_level=RiskLevel.MEDIUM,
        ),
    ),
    ServiceName.SCN: IPTEService(
        config=ServiceConfig(
            name="scn-svc", port=8014, base_url="http://localhost:8014",
            risk_level=RiskLevel.MEDIUM,
        ),
    ),
    ServiceName.NETWORK: IPTEService(
        config=ServiceConfig(
            name="network-svc", port=8015, base_url="http://localhost:8015",
            risk_level=RiskLevel.MEDIUM,
        ),
    ),
    ServiceName.ML: IPTEService(
        config=ServiceConfig(
            name="ml-svc", port=8016, base_url="http://localhost:8016",
            risk_level=RiskLevel.LOW,
        ),
        has_external_api=True,
    ),
}


BUSINESS_CRITICAL_PATHS = [
    {"name": "demand_to_schedule", "description": "Demand classification → material scoring → capacity scheduling → feasibility → resolution", "services": [ServiceName.DPE, ServiceName.MAT, ServiceName.CAP, ServiceName.FEA, ServiceName.RES], "risk": RiskLevel.CRITICAL},
    {"name": "delay_to_copilot", "description": "Delay detection → NLP classification → Copilot suggestion", "services": [ServiceName.DEL, ServiceName.NLP], "risk": RiskLevel.HIGH},
    {"name": "dsar_compliance", "description": "GDPR DSAR request → processing → completion/denial", "services": [ServiceName.DPE], "risk": RiskLevel.HIGH},
    {"name": "audit_immutability", "description": "State-changing operation → audit log write → immutability verification", "services": [ServiceName.DPE, ServiceName.CAP, ServiceName.FEA], "risk": RiskLevel.CRITICAL},
    {"name": "sop_financial_pipeline", "description": "S&OP forecast → solve → cost accounting → financial projection", "services": [ServiceName.DPE], "risk": RiskLevel.HIGH},
    {"name": "digital_twin_disruption", "description": "BOM explosion → supplier trace → disruption simulation → war room", "services": [ServiceName.NETWORK, ServiceName.ALERT], "risk": RiskLevel.MEDIUM},
]


GOVERNANCE_RULES = {
    "human_approval_required": [
        "All AI-generated tests must be reviewed by a QA engineer before merging",
        "Self-healed selector changes on critical paths require human approval",
        "AI-generated assertions must be validated against business requirements",
        "Production releases always require human sign-off",
        "Compliance-related test changes require security team review",
    ],
    "never_automate": [
        "Go/no-go release decisions",
        "Compliance audit sign-offs",
        "Customer impact assessment for P1 incidents",
        "RLS policy verification (must be manual audit)",
        "mTLS certificate rotation verification",
    ],
    "audit_requirements": [
        "All AI test generation runs must be logged with prompt, model version, and output",
        "Self-healing actions must preserve before/after selector state",
        "Visual regression baselines must be versioned and reviewable",
        "Test optimization decisions must include coverage impact analysis",
    ],
}


SUCCESS_METRICS = {
    "efficiency": {
        "regression_execution_time_target_minutes": 15,
        "test_maintenance_reduction_pct": 50,
        "automation_coverage_target_pct": 80,
        "test_creation_time_reduction_pct": 60,
    },
    "quality": {
        "escaped_defects_target_per_release": 0,
        "flaky_test_rate_target_pct": 2,
        "defect_detection_rate_target_pct": 85,
        "release_failure_rate_target_pct": 0,
    },
    "business": {
        "release_frequency_target": "weekly",
        "mttr_target_minutes": 30,
        "cost_per_release_reduction_pct": 40,
        "qa_productivity_increase_pct": 50,
    },
}