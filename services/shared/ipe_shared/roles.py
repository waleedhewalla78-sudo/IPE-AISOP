"""Phase 8 §2.3 — Role-based agent behaviour context."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


class AgentRoleContext:
    """Wraps every agent call with role-based behaviour modification."""

    ROLE_CONFIGS: dict[str, dict[str, Any]] = {
        "employee": {
            "decision_authority": "view_and_execute",
            "max_financial_impact": 1000,  # USD
            "can_approve_resolution": False,
            "can_override_ai": False,
            "financial_visibility": ["cost_impact"],
            "data_scope": "own_work_centre",
            "escalation_target": "supervisor",
            "autonomous_actions": [],
            "can_modify_autonomous_rules": False,
        },
        "supervisor": {
            "decision_authority": "approve_moderate",
            "max_financial_impact": 10000,
            "can_approve_resolution": True,
            "can_override_ai": False,
            "financial_visibility": ["cost_impact", "department_pnl"],
            "data_scope": "department",
            "escalation_target": "manager",
            "autonomous_actions": ["approve_low_risk_reschedule", "approve_standard_po"],
            "can_modify_autonomous_rules": False,
        },
        "manager": {
            "decision_authority": "approve_all",
            "max_financial_impact": 50000,
            "can_approve_resolution": True,
            "can_override_ai": True,
            "financial_visibility": ["cost_impact", "margin", "pnl", "cash_flow"],
            "data_scope": "full_plant",
            "escalation_target": "executive",
            "autonomous_actions": ["all"],
            "can_modify_autonomous_rules": True,
        },
    }

    # Map JWT / app roles onto Phase 8 agent roles
    ROLE_ALIASES: dict[str, str] = {
        "employee": "employee",
        "operator": "employee",
        "viewer": "employee",
        "planner": "supervisor",
        "supervisor": "supervisor",
        "manager": "manager",
        "admin": "manager",
        "executive": "manager",
    }

    @classmethod
    def normalize_role(cls, user_role: str) -> str:
        key = (user_role or "employee").strip().lower()
        return cls.ROLE_ALIASES.get(key, "employee")

    @classmethod
    def get_context(cls, user_role: str, agent_id: str = "") -> dict[str, Any]:
        role = cls.normalize_role(user_role)
        base = deepcopy(cls.ROLE_CONFIGS.get(role, cls.ROLE_CONFIGS["employee"]))
        # A11 financial — only managers see full financials
        if agent_id == "A11" and role != "manager":
            base["financial_visibility"] = ["cost_impact"]
        base["role"] = role
        base["agent_id"] = agent_id
        return base

    @classmethod
    def can_execute(cls, user_role: str, action: str, financial_impact: float) -> bool:
        config = cls.get_context(user_role)
        if financial_impact > float(config["max_financial_impact"]):
            return False
        if action == "approve_resolution" and not config["can_approve_resolution"]:
            return False
        if action == "override_ai" and not config["can_override_ai"]:
            return False
        if action == "autonomous" and not config["autonomous_actions"]:
            return False
        return True

    @classmethod
    def filter_financials(
        cls, user_role: str, payload: dict[str, Any], *, agent_id: str = ""
    ) -> dict[str, Any]:
        """Strip financial fields the role must not see."""
        ctx = cls.get_context(user_role, agent_id)
        visibility = set(ctx.get("financial_visibility") or [])
        out = dict(payload)
        if "margin" not in visibility:
            out.pop("margin", None)
            out.pop("margin_pct", None)
        if "pnl" not in visibility and "department_pnl" not in visibility:
            out.pop("pnl", None)
            out.pop("department_pnl", None)
        if "cash_flow" not in visibility:
            out.pop("cash_flow", None)
        if "cost_impact" not in visibility:
            out.pop("cost_impact", None)
            out.pop("cost", None)
        return out

    @classmethod
    def escalation_required(cls, user_role: str, financial_impact: float) -> bool:
        config = cls.get_context(user_role)
        return financial_impact > float(config["max_financial_impact"])
