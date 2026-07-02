"""Planner Copilot Lite — keyword/regex intent router (no LLM required)."""

from __future__ import annotations

import re
from enum import Enum


class PlannerIntent(str, Enum):
    AT_RISK_MOS = "at_risk_mos"
    MO_DETAIL = "mo_detail"
    SCENARIO_LIST = "scenario_list"
    SYNC_STATUS = "sync_status"
    SCHEDULE_SUMMARY = "schedule_summary"
    UNKNOWN = "unknown"


_INTENT_PATTERNS: list[tuple[PlannerIntent, list[str]]] = [
    (
        PlannerIntent.SYNC_STATUS,
        [r"\bsync\b", r"\bodoo\b", r"last import", r"erp status", r"import status"],
    ),
    (
        PlannerIntent.SCENARIO_LIST,
        [r"\bscenario", r"\bresolution", r"\bmitigation", r"\boptions\b", r"proposed"],
    ),
    (
        PlannerIntent.SCHEDULE_SUMMARY,
        [r"\bschedule", r"\bcapacity\b", r"\bbottleneck", r"work center", r"utilization"],
    ),
    (
        PlannerIntent.MO_DETAIL,
        [r"\bmo[- ]?\w+", r"manufacturing order", r"tell me about", r"details for"],
    ),
    (
        PlannerIntent.AT_RISK_MOS,
        [r"at risk", r"risky", r"which.*order", r"low feasibility", r"\bcritical\b", r"below"],
    ),
]

_MO_ID_RE = re.compile(r"\b(?:mo[- ]?)?([a-z0-9-]{4,})\b", re.I)


def detect_intent(query: str) -> PlannerIntent:
    q = query.lower().strip()
    if not q:
        return PlannerIntent.UNKNOWN
    for intent, patterns in _INTENT_PATTERNS:
        for pat in patterns:
            if re.search(pat, q):
                return intent
    return PlannerIntent.AT_RISK_MOS


def extract_mo_ref(query: str) -> str | None:
    skip = {"which", "what", "tell", "about", "order", "orders", "risk", "show", "last", "sync"}
    for match in _MO_ID_RE.finditer(query):
        token = match.group(1)
        if token.lower() not in skip:
            return token
    return None
