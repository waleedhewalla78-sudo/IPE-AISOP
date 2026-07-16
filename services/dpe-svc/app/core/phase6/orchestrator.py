"""A17 Cross-Functional Orchestrator — the meta-agent.

Resolves conflicts between domain agents using a priority hierarchy, enforces
six enterprise-wide policies, processes cascading events, and coordinates the
cross-functional ATP/CTP decision (A1/A3/A11/A13).

Pure-logic core; deterministic and fully unit-testable. Governance levels 1-4
mirror the doc's autonomy model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar

from app.core.phase4.finance_intel import evaluate_decision_pnl
from app.core.phase5.atp_ctp import promise_order
from app.core.phase6.commercial_intel import optimize_price

# Governance autonomy levels (doc §4.3).
GOV_AUTONOMOUS = 1
GOV_SUPERVISED = 2
GOV_APPROVED = 3
GOV_ESCALATED = 4


@dataclass
class AgentRecommendation:
    """A domain agent's preferred option and its weighted impacts.

    ``impacts`` maps a resolution dimension (e.g. ``customer_sla``) to a signed
    score in roughly [-1, 1] where positive = the option advances that
    dimension.
    """

    agent_id: str
    action: str
    impacts: dict[str, float] = field(default_factory=dict)
    direct_cost: float = 0.0
    requires_human_approval: bool = False
    approval_role: str | None = None


class CrossFunctionalOrchestrator:
    """A17: resolves conflicts, enforces policy, coordinates cascades."""

    agent_id = "A17"
    name = "Cross-Functional Orchestrator"

    # When agents disagree, this hierarchy determines priority (doc §2.2).
    RESOLUTION_HIERARCHY: ClassVar[dict[str, int]] = {
        "safety": 100,
        "customer_sla": 90,
        "revenue_protection": 80,
        "margin_protection": 70,
        "cost_optimization": 60,
        "efficiency": 50,
        "sustainability": 40,
    }

    # ---- Conflict resolution -------------------------------------------------

    def resolve_conflict(
        self,
        recommendations: list[AgentRecommendation],
        *,
        reversal_window_hours: int = 4,
    ) -> dict[str, Any]:
        """Score each recommendation by hierarchy-weighted impact; pick winner."""
        if not recommendations:
            return {"agent_id": self.agent_id, "decision": None, "reason": "no_recommendations"}

        scored: list[dict[str, Any]] = []
        for rec in recommendations:
            score = 0.0
            for dimension, impact in rec.impacts.items():
                priority = self.RESOLUTION_HIERARCHY.get(dimension, 50)
                score += priority * impact
            scored.append({"recommendation": rec, "score": round(score, 2)})

        scored.sort(key=lambda s: s["score"], reverse=True)
        winner = scored[0]["recommendation"]
        rationale = [
            f"{s['recommendation'].agent_id}:{s['recommendation'].action} → score {s['score']}"
            for s in scored
        ]

        if winner.requires_human_approval:
            return {
                "agent_id": self.agent_id,
                "mode": "escalation",
                "governance_level": GOV_APPROVED,
                "winner": {"agent_id": winner.agent_id, "action": winner.action},
                "escalate_to": winner.approval_role or "ops_director",
                "rationale": rationale,
                "scores": [
                    {"agent": s["recommendation"].agent_id, "score": s["score"]} for s in scored
                ],
            }

        return {
            "agent_id": self.agent_id,
            "mode": "autonomous",
            "governance_level": GOV_AUTONOMOUS,
            "winner": {"agent_id": winner.agent_id, "action": winner.action},
            "reversible": True,
            "reversal_window_hours": reversal_window_hours,
            "rationale": rationale,
            "scores": [
                {"agent": s["recommendation"].agent_id, "score": s["score"]} for s in scored
            ],
        }

    # ---- Enterprise policy enforcement --------------------------------------

    def enforce_policies(self, context: dict[str, Any]) -> dict[str, Any]:
        """Evaluate the 6 enterprise policies against a decision context.

        Returns per-policy verdicts and an overall gate: ``allow``, ``review``,
        or ``block``. ``block`` (quality/margin hard gates) dominates.
        """
        results: list[dict[str, Any]] = []

        # POLICY 1 — Customer Priority Override.
        cust_tier = str(context.get("customer_tier", "B")).upper()
        order_margin_pct = float(context.get("order_margin_pct", 100.0))
        p1_ok = True
        p1_note = "No A-customer capacity conflict."
        if context.get("capacity_conflict"):
            if cust_tier == "A" and order_margin_pct >= 10:
                p1_note = "A-customer prioritized in capacity conflict."
            elif cust_tier == "A":
                p1_ok = False
                p1_note = "A-customer order margin < 10% — priority override does NOT apply."
        results.append(
            {
                "policy": "P1_customer_priority",
                "status": "ok" if p1_ok else "review",
                "note": p1_note,
            }
        )

        # POLICY 2 — Cash Flow Protection (committed PO ≤ 60% of reserves).
        committed = float(context.get("committed_po_value", 0.0))
        reserves = float(context.get("cash_reserves", 1.0))
        ratio = committed / reserves if reserves else 1.0
        p2_ok = ratio <= 0.60
        results.append(
            {
                "policy": "P2_cash_flow_protection",
                "status": "ok" if p2_ok else "review",
                "note": f"Committed PO {ratio * 100:.0f}% of reserves (limit 60%).",
            }
        )

        # POLICY 3 — Single-Source Risk (no material > 80% from one supplier).
        max_share = float(context.get("max_supplier_share_pct", 0.0))
        p3_ok = max_share <= 80.0
        results.append(
            {
                "policy": "P3_single_source_risk",
                "status": "ok" if p3_ok else "review",
                "note": (
                    f"Top supplier share {max_share:.0f}% (limit 80%) — "
                    "dual-source if exceeded."
                ),
            }
        )

        # POLICY 4 — Margin Floor (hard block unless strategic + board approval).
        margin_floor = float(context.get("margin_floor_pct", 15.0))
        strategic = bool(context.get("strategic_customer", False))
        board_approved = bool(context.get("board_approved", False))
        if order_margin_pct >= margin_floor:
            p4_status = "ok"
            p4_note = f"Margin {order_margin_pct}% ≥ floor {margin_floor}%."
        elif strategic and board_approved:
            p4_status = "review"
            p4_note = "Below floor but strategic customer with board approval."
        else:
            p4_status = "block"
            p4_note = f"Margin {order_margin_pct}% below floor {margin_floor}% — order blocked."
        results.append({"policy": "P4_margin_floor", "status": p4_status, "note": p4_note})

        # POLICY 5 — Sustainability Commitment (carbon must trend down 5% YoY).
        carbon_delta = float(context.get("carbon_delta_pct", 0.0))
        if carbon_delta <= -5.0:
            p5_status, p5_note = "ok", f"Carbon {carbon_delta}% YoY meets -5% commitment."
        elif carbon_delta <= 0:
            p5_status, p5_note = "ok", f"Carbon {carbon_delta}% YoY (below target reduction)."
        else:
            p5_status, p5_note = "review", f"Carbon +{carbon_delta}% — justification required."
        results.append({"policy": "P5_sustainability", "status": p5_status, "note": p5_note})

        # POLICY 6 — Quality Non-Negotiable (defect prob > 20% → inspection hold).
        defect_prob = float(context.get("defect_probability_pct", 0.0))
        if defect_prob > 20.0:
            p6_status = "block"
            p6_note = (
                f"Defect probability {defect_prob}% > 20% — "
                "mandatory inspection hold (Quality Manager sign-off)."
            )
        else:
            p6_status = "ok"
            p6_note = f"Defect probability {defect_prob}% within tolerance."
        results.append(
            {"policy": "P6_quality_non_negotiable", "status": p6_status, "note": p6_note}
        )

        statuses = {r["status"] for r in results}
        if "block" in statuses:
            gate = "block"
        elif "review" in statuses:
            gate = "review"
        else:
            gate = "allow"

        return {
            "agent_id": self.agent_id,
            "capability": "enterprise_policy_enforcement",
            "gate": gate,
            "policies": results,
        }

    # ---- Cascading events ----------------------------------------------------

    def cascade_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Process a cross-functional cascade (e.g. a demand change).

        Produces an ordered chain of coordinated agent steps with an elapsed
        estimate — the doc's "09:00 cascade resolved by 09:05" pattern.
        """
        event_type = event.get("type", "demand_change")
        product = event.get("product_id", "FG-DT100")
        delta_units = float(event.get("delta_units", 38))

        steps = [
            {
                "seq": 1,
                "agent": "A1",
                "domain": "demand",
                "action": f"Register +{delta_units} units {product}; fuse signal",
            },
            {
                "seq": 2,
                "agent": "A2",
                "domain": "inventory",
                "action": "Check FG + raw material availability; safety-stock impact",
            },
            {
                "seq": 3,
                "agent": "A3",
                "domain": "production",
                "action": "Capacity check + smart-batch into existing schedule",
            },
            {
                "seq": 4,
                "agent": "A9",
                "domain": "procurement",
                "action": "Recommend expedite/alt-source for short materials",
            },
            {
                "seq": 5,
                "agent": "A11",
                "domain": "finance",
                "action": "Margin + expedite-cost + cash impact",
            },
            {
                "seq": 6,
                "agent": "A13",
                "domain": "commercial",
                "action": "Reprice/confirm deal profitability",
            },
            {
                "seq": 7,
                "agent": "A8",
                "domain": "customer",
                "action": "Draft proactive delivery notification",
            },
        ]
        elapsed_seconds = len(steps) * 1  # symbolic: seconds, not days

        return {
            "agent_id": self.agent_id,
            "capability": "cascading_events",
            "event_type": event_type,
            "product_id": product,
            "delta_units": delta_units,
            "coordinated_agents": [s["agent"] for s in steps],
            "chain": steps,
            "estimated_elapsed_seconds": elapsed_seconds,
            "resolution": "coordinated_plan_ready",
        }

    # ---- Cross-functional ATP/CTP (headline scenario) -----------------------

    def orchestrate_atp(
        self,
        *,
        order_id: str = "SO-2026-0289",
        product_id: str = "FG-DT250",
        customer_id: str = "CUST-SEC",
        customer_tier: str = "A",
        qty: float = 50,
        requested_date: str = "2026-08-10",
        inventory_available: float = 12,
        capacity_available_hrs: float = 95,
        hours_per_unit: float = 2.5,
        unit_cost: float = 64_400.0,
        list_price: float = 85_000.0,
        material_lead_days: int = 8,
        expedite_cost: float = 2_400.0,
        penalty_avoided: float = 6_000.0,
        margin_floor_pct: float = 15.0,
        defect_probability_pct: float = 5.0,
        strategic_customer: bool = True,
    ) -> dict[str, Any]:
        """Coordinate A1(demand)+A3(capacity)+A11(finance)+A13(commercial)+A17.

        Fuses commercial pricing, promise feasibility, finance P&L, and the
        enterprise policy gate into one order-acceptance decision.
        """
        # A13 — commercial pricing.
        pricing = optimize_price(
            product_id=product_id,
            customer_id=customer_id,
            customer_tier=customer_tier,
            list_price=list_price,
            unit_cost=unit_cost,
            quantity=int(qty),
            margin_floor_pct=margin_floor_pct,
        )
        unit_price = pricing["recommended_price"]

        # A1/A3 — ATP/CTP promise feasibility (Phase 5 core).
        promise = promise_order(
            order_id=order_id,
            product_id=product_id,
            qty=qty,
            requested_date=requested_date,
            inventory_available=inventory_available,
            capacity_available_hrs=capacity_available_hrs,
            hours_per_unit=hours_per_unit,
            unit_cost=unit_cost,
            unit_price=unit_price,
            material_lead_days=material_lead_days,
        )

        # A11 — decision P&L (expedite vs penalty avoided).
        pnl = evaluate_decision_pnl(
            decision="expedite_materials_to_hold_date",
            direct_cost=expedite_cost,
            revenue_protected=qty * unit_price,
            penalty_avoided=penalty_avoided,
        )

        order_margin_pct = pricing["margin_pct"]

        # A17 — enterprise policy gate.
        policy = self.enforce_policies(
            {
                "customer_tier": customer_tier,
                "order_margin_pct": order_margin_pct,
                "capacity_conflict": not promise["checks"]["capacity_ok"],
                "margin_floor_pct": margin_floor_pct,
                "strategic_customer": strategic_customer,
                "board_approved": strategic_customer,
                "defect_probability_pct": defect_probability_pct,
            }
        )

        # Final decision: promise must be viable AND policy gate not blocking.
        if policy["gate"] == "block":
            decision = "reject"
            governance = GOV_ESCALATED
        elif promise["status"] in ("accept", "accept_with_delay") and policy["gate"] in (
            "allow",
            "review",
        ):
            decision = "accept"
            governance = GOV_SUPERVISED if policy["gate"] == "review" else GOV_AUTONOMOUS
        else:
            decision = "negotiate"
            governance = GOV_APPROVED

        return {
            "agent_id": self.agent_id,
            "capability": "cross_functional_atp",
            "order_id": order_id,
            "coordinated_agents": ["A1", "A3", "A11", "A13", "A17"],
            "decision": decision,
            "governance_level": governance,
            "commercial": {
                "recommended_price": unit_price,
                "margin_pct": order_margin_pct,
                "revenue": round(qty * unit_price, 2),
            },
            "promise": {
                "status": promise["status"],
                "promised_date": promise["promised_date"],
                "delay_days": promise["delay_days"],
                "bottleneck": promise["bottleneck"],
                "from_stock": promise["breakdown"]["from_stock"],
                "from_production": promise["breakdown"]["from_production"],
            },
            "finance": {
                "expedite_cost": expedite_cost,
                "net_impact": pnl["net_impact"],
                "roi": pnl["roi"],
                "recommendation": pnl["recommendation"],
            },
            "policy_gate": policy["gate"],
            "policies": policy["policies"],
        }
