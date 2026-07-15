"""Phase 4 premium core package — A8/A11/autonomy/pulse."""

from app.core.phase4.autonomous_rules import AutonomousRuleEngine
from app.core.phase4.command_pulse import build_intelligence_pulse
from app.core.phase4.customer_intel import (
    CustomerIntelligence,
    draft_delay_notification,
    score_customer_health,
)
from app.core.phase4.finance_intel import FinanceIntelligence

__all__ = [
    "AutonomousRuleEngine",
    "CustomerIntelligence",
    "FinanceIntelligence",
    "build_intelligence_pulse",
    "draft_delay_notification",
    "score_customer_health",
]
