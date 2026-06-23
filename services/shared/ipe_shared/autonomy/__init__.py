"""IPE Autonomy module — Progressive Autonomy state machine and safety guardrail."""
from ipe_shared.autonomy.state_machine import (
    AutonomyState,
    AutonomyAction,
    AutonomyConfig,
    AutonomyDecision,
    AutonomyStateMachine,
    get_autonomy_state_machine,
)
from ipe_shared.autonomy.guardrail import SafetyGuardrail, GuardrailResult

__all__ = [
    "AutonomyState",
    "AutonomyAction",
    "AutonomyConfig",
    "AutonomyDecision",
    "AutonomyStateMachine",
    "get_autonomy_state_machine",
    "SafetyGuardrail",
    "GuardrailResult",
]
