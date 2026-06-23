"""Progressive Autonomy state machine for IPE scheduling decisions.

States: Shadow → Suggest → Autonomous
Per-tenant configuration via Unleash feature flags.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger("ipe.autonomy")


class AutonomyState(StrEnum):
    SHADOW = "shadow"
    SUGGEST = "suggest"
    AUTONOMOUS = "autonomous"


class AutonomyAction(StrEnum):
    ENTER_SHADOW = "enter_shadow"
    ENTER_SUGGEST = "enter_suggest"
    ENTER_AUTONOMOUS = "enter_autonomous"
    BLOCK_AUTONOMOUS = "block_autonomous"


VALID_TRANSITIONS: dict[AutonomyState, set[AutonomyState]] = {
    AutonomyState.SHADOW: {AutonomyState.SUGGEST},
    AutonomyState.SUGGEST: {AutonomyState.SHADOW, AutonomyState.AUTONOMOUS},
    AutonomyState.AUTONOMOUS: {AutonomyState.SUGGEST},
}


@dataclass
class AutonomyConfig:
    tenant_id: str
    state: AutonomyState = AutonomyState.SHADOW
    feasibility_threshold: float = 85.0
    max_tardiness_minutes: int = 60
    require_approval_above: float = 90.0
    enabled: bool = True
    last_transition: str = ""
    transition_reason: str = ""


@dataclass
class AutonomyDecision:
    action_taken: str
    feasibility_score: float
    current_state: AutonomyState
    blocked: bool = False
    block_reason: str = ""
    requires_approval: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class AutonomyStateMachine:
    def __init__(self) -> None:
        self._configs: dict[str, AutonomyConfig] = {}

    def get_config(self, tenant_id: str) -> AutonomyConfig:
        if tenant_id not in self._configs:
            self._configs[tenant_id] = AutonomyConfig(tenant_id=tenant_id)
        return self._configs[tenant_id]

    def transition(self, tenant_id: str, target_state: AutonomyState, reason: str = "") -> bool:
        config = self.get_config(tenant_id)
        valid_targets = VALID_TRANSITIONS.get(config.state, set())
        if target_state not in valid_targets:
            logger.warning(
                "Invalid transition for tenant %s: %s → %s (valid: %s)",
                tenant_id, config.state, target_state, valid_targets,
            )
            return False

        old_state = config.state
        config.state = target_state
        config.last_transition = datetime.now(UTC).isoformat()
        config.transition_reason = reason
        logger.info("Autonomy transition: tenant=%s %s → %s (reason: %s)", tenant_id, old_state, target_state, reason)
        return True

    def evaluate(self, tenant_id: str, feasibility_score: float) -> AutonomyDecision:
        config = self.get_config(tenant_id)
        if not config.enabled:
            return AutonomyDecision(
                action_taken=AutonomyAction.ENTER_SHADOW.value,
                feasibility_score=feasibility_score,
                current_state=config.state,
                blocked=True,
                block_reason="Autonomy disabled for tenant",
            )

        if config.state == AutonomyState.SHADOW:
            return AutonomyDecision(
                action_taken="shadow_observed",
                feasibility_score=feasibility_score,
                current_state=config.state,
                metadata={"note": "AI recommendation logged, human decides"},
            )

        if config.state == AutonomyState.SUGGEST:
            if feasibility_score >= config.require_approval_above:
                return AutonomyDecision(
                    action_taken="suggest_recommend",
                    feasibility_score=feasibility_score,
                    current_state=config.state,
                    requires_approval=True,
                    metadata={"note": "High-value MO requires planner approval"},
                )
            if feasibility_score >= config.feasibility_threshold:
                return AutonomyDecision(
                    action_taken="suggest_recommend",
                    feasibility_score=feasibility_score,
                    current_state=config.state,
                    metadata={"note": "Recommendation ready for planner review"},
                )
            return AutonomyDecision(
                action_taken="suggest_low_score",
                feasibility_score=feasibility_score,
                current_state=config.state,
                blocked=True,
                block_reason=f"Feasibility {feasibility_score:.1f}% below threshold {config.feasibility_threshold}%",
            )

        if config.state == AutonomyState.AUTONOMOUS:
            if feasibility_score < config.feasibility_threshold:
                return AutonomyDecision(
                    action_taken="autonomous_block",
                    feasibility_score=feasibility_score,
                    current_state=config.state,
                    blocked=True,
                    block_reason=f"Feasibility {feasibility_score:.1f}% below threshold {config.feasibility_threshold}% — synchronous block",
                )
            return AutonomyDecision(
                action_taken="autonomous_confirm",
                feasibility_score=feasibility_score,
                current_state=config.state,
                metadata={"note": "Auto-confirmed by autonomous mode"},
            )

        return AutonomyDecision(
            action_taken="unknown_state",
            feasibility_score=feasibility_score,
            current_state=config.state,
            blocked=True,
            block_reason=f"Unknown state: {config.state}",
        )


_state_machine = AutonomyStateMachine()


def get_autonomy_state_machine() -> AutonomyStateMachine:
    return _state_machine
