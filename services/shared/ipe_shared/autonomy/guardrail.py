"""Safety guardrail for synchronous ERP write-back blocking.

When feasibility < threshold, blocks write-back synchronously.
Async Kafka alert sent to Slack/Teams.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ipe_shared.autonomy.state_machine import AutonomyDecision, AutonomyStateMachine

logger = logging.getLogger("ipe.autonomy.guardrail")


@dataclass
class GuardrailResult:
    allowed: bool
    feasibility_score: float
    threshold: float
    reason: str = ""
    decision: AutonomyDecision | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SafetyGuardrail:
    def __init__(
        self,
        state_machine: AutonomyStateMachine,
        default_threshold: float = 85.0,
    ) -> None:
        self.state_machine = state_machine
        self.default_threshold = default_threshold

    def check_write_back(
        self,
        tenant_id: str,
        mo_id: str,
        feasibility_score: float,
        threshold: float | None = None,
    ) -> GuardrailResult:
        effective_threshold = threshold or self.default_threshold
        decision = self.state_machine.evaluate(tenant_id, feasibility_score)

        if decision.blocked:
            logger.warning(
                "Write-back BLOCKED for MO %s: tenant=%s score=%.1f%% reason=%s",
                mo_id, tenant_id, feasibility_score, decision.block_reason,
            )
            return GuardrailResult(
                allowed=False,
                feasibility_score=feasibility_score,
                threshold=effective_threshold,
                reason=decision.block_reason,
                decision=decision,
            )

        if feasibility_score < effective_threshold:
            logger.warning(
                "Write-back BLOCKED for MO %s: score=%.1f%% < threshold=%.1f%%",
                mo_id, feasibility_score, effective_threshold,
            )
            return GuardrailResult(
                allowed=False,
                feasibility_score=feasibility_score,
                threshold=effective_threshold,
                reason=f"Feasibility {feasibility_score:.1f}% below threshold {effective_threshold}%",
                decision=decision,
            )

        logger.info(
            "Write-back ALLOWED for MO %s: score=%.1f%% state=%s action=%s",
            mo_id, feasibility_score, decision.current_state, decision.action_taken,
        )
        return GuardrailResult(
            allowed=True,
            feasibility_score=feasibility_score,
            threshold=effective_threshold,
            decision=decision,
            metadata={"action_taken": decision.action_taken},
        )
