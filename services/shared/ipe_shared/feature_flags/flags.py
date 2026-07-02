"""Unleash feature flag definitions for IPE Progressive Autonomy.

Pre-configured feature flags for:
- Progressive Autonomy (Shadow → Suggest → Autonomous)
- Per-tenant configuration
- Circuit breakers
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FeatureFlag:
    name: str
    enabled: bool
    description: str
    strategies: list[dict[str, Any]] = field(default_factory=list)
    variants: list[dict[str, Any]] = field(default_factory=list)


IPE_FEATURE_FLAGS: list[FeatureFlag] = [
    FeatureFlag(
        name="ipe.progressive_autonomy",
        enabled=True,
        description="Enable Progressive Autonomy for scheduling decisions",
        strategies=[{
            "name": "default",
            "parameters": {},
        }],
    ),
    FeatureFlag(
        name="ipe.autonomy.shadow",
        enabled=True,
        description="Shadow mode: AI recommends, human decides",
        strategies=[{
            "name": "default",
            "parameters": {"enabled": "true"},
        }],
    ),
    FeatureFlag(
        name="ipe.autonomy.suggest",
        enabled=True,
        description="Suggest mode: AI proposes, planner approves",
        strategies=[{
            "name": "default",
            "parameters": {"enabled": "true"},
        }],
    ),
    FeatureFlag(
        name="ipe.autonomy.autonomous",
        enabled=False,
        description="Autonomous mode: AI confirms, human monitors",
        strategies=[{
            "name": "default",
            "parameters": {"enabled": "false"},
        }],
    ),
    FeatureFlag(
        name="ipe.xai.enabled",
        enabled=True,
        description="Enable XAI explanations on all scoring endpoints",
        strategies=[{
            "name": "default",
            "parameters": {"enabled": "true"},
        }],
    ),
    FeatureFlag(
        name="ipe.pii.stripping",
        enabled=True,
        description="Enable PII stripping in NLP copilot",
        strategies=[{
            "name": "default",
            "parameters": {"enabled": "true"},
        }],
    ),
    FeatureFlag(
        name="ipe.llm.tiered_routing",
        enabled=False,
        description="Enable tiered LLM routing (SAAS/PRIVATE_VPC/ON_PREM)",
        strategies=[{
            "name": "default",
            "parameters": {"enabled": "false"},
        }],
    ),
    FeatureFlag(
        name="ipe.energy.green_scheduling",
        enabled=True,
        description="Enable carbon-aware green scheduling",
        strategies=[{
            "name": "default",
            "parameters": {"enabled": "true"},
        }],
    ),
    FeatureFlag(
        name="ipe.circuit_breaker.kafka",
        enabled=True,
        description="Circuit breaker for Kafka producer failures",
        strategies=[{
            "name": "default",
            "parameters": {"failure_threshold": "5", "reset_timeout_s": "60"},
        }],
    ),
    FeatureFlag(
        name="ipe.circuit_breaker.database",
        enabled=True,
        description="Circuit breaker for database connection failures",
        strategies=[{
            "name": "default",
            "parameters": {"failure_threshold": "3", "reset_timeout_s": "30"},
        }],
    ),
    FeatureFlag(
        name="ipe.ui.dark_mode",
        enabled=True,
        description="Dark mode for IPE frontend",
        strategies=[{
            "name": "default",
            "parameters": {"enabled": "true"},
        }],
    ),
    FeatureFlag(
        name="ipe.ui.war_room",
        enabled=True,
        description="War Room disruption dashboard",
        strategies=[{
            "name": "default",
            "parameters": {"enabled": "true"},
        }],
    ),
    FeatureFlag(
        name="ipe.odoo.resolution_writeback",
        enabled=False,
        description="Post Odoo chatter / draft PO when a resolution scenario is approved",
        strategies=[{
            "name": "default",
            "parameters": {"enabled": "false"},
        }],
    ),
]


class LocalFeatureFlags:
    """Local feature flag store for development/demo without Unleash server."""

    def __init__(self) -> None:
        self._flags: dict[str, bool] = {f.name: f.enabled for f in IPE_FEATURE_FLAGS}

    def is_enabled(self, flag_name: str) -> bool:
        return self._flags.get(flag_name, False)

    def set_enabled(self, flag_name: str, enabled: bool) -> None:
        self._flags[flag_name] = enabled

    def list_flags(self) -> dict[str, bool]:
        return dict(self._flags)


_local_flags: LocalFeatureFlags | None = None


def get_feature_flags() -> LocalFeatureFlags:
    global _local_flags
    if _local_flags is None:
        _local_flags = LocalFeatureFlags()
    return _local_flags
