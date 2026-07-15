"""Autonomous planning rules with configurable guardrails (Phase 4 Premium)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class AutonomousAction:
    action_id: str
    rule_id: str
    status: str  # applied | skipped | blocked
    summary: str
    reversible: bool = True
    override_hours: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AutonomousRuleEngine:
    """
    RULE 1 Auto-approve low-risk resolutions
    RULE 2 Auto-generate POs
    RULE 3 Auto-batch production
    RULE 4 Auto-escalate quality alerts
    """

    def __init__(
        self,
        *,
        max_po_value: float = 50_000.0,
        min_supplier_reliability: float = 0.80,
        quality_risk_threshold: float = 0.15,
    ) -> None:
        self.max_po_value = max_po_value
        self.min_supplier_reliability = min_supplier_reliability
        self.quality_risk_threshold = quality_risk_threshold
        self._log: list[AutonomousAction] = []

    def evaluate_overnight(self, context: dict[str, Any]) -> dict[str, Any]:
        actions: list[AutonomousAction] = []
        for res in context.get("resolutions", []):
            actions.append(self._rule_auto_approve(res))
        for po in context.get("reorder_candidates", []):
            actions.append(self._rule_auto_po(po))
        for batch in context.get("batch_candidates", []):
            actions.append(self._rule_auto_batch(batch))
        for q in context.get("quality_risks", []):
            actions.append(self._rule_quality_escalate(q))

        applied = [a for a in actions if a.status == "applied"]
        self._log.extend(actions)
        return {
            "actions_taken": len(applied),
            "actions": [a.__dict__ for a in actions],
            "planner_summary": self._summarize(applied),
        }

    def _rule_auto_approve(self, res: dict[str, Any]) -> AutonomousAction:
        aid = str(uuid4())
        priority = str(res.get("customer_priority", "C")).upper()
        delay = float(res.get("delay_days", 99))
        cost = float(res.get("cost", 999))
        score = float(res.get("feasibility_score", 100))
        if priority == "A":
            return AutonomousAction(
                aid, "RULE1_AUTO_APPROVE", "blocked",
                "Never auto-approve for A-priority customers",
                metadata={"guardrail": "A_customer"},
            )
        if score < 70 and cost == 0 and delay <= 2 and priority in {"B", "C"}:
            return AutonomousAction(
                aid, "RULE1_AUTO_APPROVE", "applied",
                f"Auto-approved reschedule for {res.get('mo_id')} (+{delay}d, $0)",
                override_hours=4,
                metadata=res,
            )
        return AutonomousAction(
            aid, "RULE1_AUTO_APPROVE", "skipped",
            "Resolution does not meet low-risk criteria",
            metadata=res,
        )

    def _rule_auto_po(self, po: dict[str, Any]) -> AutonomousAction:
        aid = str(uuid4())
        value = float(po.get("po_value", 0))
        reliability = float(po.get("supplier_reliability", 0))
        if reliability < 0.70:
            return AutonomousAction(
                aid, "RULE2_AUTO_PO", "blocked",
                "Never auto-order from suppliers with score < 70",
                metadata={"guardrail": "supplier_score"},
            )
        if reliability >= self.min_supplier_reliability and value <= self.max_po_value and po.get("below_reorder"):
            return AutonomousAction(
                aid, "RULE2_AUTO_PO", "applied",
                f"Auto-created draft PO for {po.get('material_id')} (${value:,.0f})",
                override_hours=24,
                metadata=po,
            )
        return AutonomousAction(
            aid, "RULE2_AUTO_PO", "skipped",
            "PO candidate outside auto thresholds",
            metadata=po,
        )

    def _rule_auto_batch(self, batch: dict[str, Any]) -> AutonomousAction:
        aid = str(uuid4())
        savings_min = float(batch.get("changeover_savings_min", 0))
        same_priority = bool(batch.get("same_priority_level", False))
        no_date_violation = bool(batch.get("no_delivery_violation", False))
        if savings_min > 30 and same_priority and no_date_violation:
            return AutonomousAction(
                aid, "RULE3_AUTO_BATCH", "applied",
                f"Auto-batched {batch.get('product_family')} (saved {savings_min:.0f} min)",
                metadata=batch,
            )
        if not same_priority:
            return AutonomousAction(
                aid, "RULE3_AUTO_BATCH", "blocked",
                "Never batch across different customer priorities",
                metadata={"guardrail": "priority_mix"},
            )
        return AutonomousAction(
            aid, "RULE3_AUTO_BATCH", "skipped",
            "Batch candidate below savings or violates dates",
            metadata=batch,
        )

    def _rule_quality_escalate(self, q: dict[str, Any]) -> AutonomousAction:
        aid = str(uuid4())
        risk = float(q.get("defect_probability", 0))
        priority = str(q.get("customer_priority", "C")).upper()
        if risk > self.quality_risk_threshold and priority == "A":
            return AutonomousAction(
                aid, "RULE4_QUALITY_ESCALATE", "applied",
                f"Added incoming inspection for {q.get('mo_id')} (risk {risk:.0%})",
                metadata={**q, "stops_production": False},
            )
        return AutonomousAction(
            aid, "RULE4_QUALITY_ESCALATE", "skipped",
            "Quality risk below escalate criteria",
            metadata=q,
        )

    @staticmethod
    def _summarize(applied: list[AutonomousAction]) -> str:
        if not applied:
            return "No autonomous actions overnight."
        lines = [f"✓ {a.summary}" for a in applied]
        return f"{len(applied)} autonomous actions taken overnight:\n" + "\n".join(lines) + "\nAll logged. All reversible."
