"""Phase 6 Enterprise Agentic Platform cores — agents A13-A17.

- A13 Commercial Intelligence (SD-equivalent)
- A14 Analytics Intelligence (SAC-equivalent)
- A15 Procurement Execution (MM-execution)
- A16 Shop Floor Intelligence (PP-execution)
- A17 Cross-Functional Orchestrator (meta-agent)

Live-integration-dependent capabilities (Odoo Accounting, market data, IoT,
Odoo write-back) are SCAFFOLD/MOCK — PH1-02 remains OPEN.
"""

from app.core.phase6.analytics_intel import (
    AnalyticsIntelligence,
    build_predictions,
    detect_anomaly,
    detect_trend,
    generate_insights,
    predict_next,
)
from app.core.phase6.commercial_intel import (
    CommercialIntelligence,
    analyze_deal_profitability,
    check_contract_compliance,
    optimize_price,
)
from app.core.phase6.odoo_accounting import OdooAccountingConnector
from app.core.phase6.orchestrator import (
    AgentRecommendation,
    CrossFunctionalOrchestrator,
)
from app.core.phase6.procurement_exec import (
    ProcurementExecution,
    confirm_receipt,
    three_way_match,
)
from app.core.phase6.shop_floor import (
    ShopFloorIntelligence,
    build_work_instructions,
    production_progress,
    track_time,
)

__all__ = [
    "AgentRecommendation",
    "AnalyticsIntelligence",
    "CommercialIntelligence",
    "CrossFunctionalOrchestrator",
    "OdooAccountingConnector",
    "ProcurementExecution",
    "ShopFloorIntelligence",
    "analyze_deal_profitability",
    "build_predictions",
    "build_work_instructions",
    "check_contract_compliance",
    "confirm_receipt",
    "detect_anomaly",
    "detect_trend",
    "generate_insights",
    "optimize_price",
    "predict_next",
    "production_progress",
    "three_way_match",
    "track_time",
]
