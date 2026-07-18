"""S&OP interactive stage-gate scaffold (closes E2E-SOP-03 scaffolding).

In-memory cycle state machine. Durable SopStageGate rows remain available for
Wave 2 DB wiring; this module provides the interactive advance/skip API surface.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

STAGES = (
    "demand_review",
    "supply_review",
    "reconciliation",
    "management_review",
    "closed",
)


class SopStageGateMachine:
    """Deterministic stage-gate for a single S&OP cycle."""

    def __init__(self, *, cycle_name: str = "monthly") -> None:
        self.cycle_id = f"SOP-{uuid.uuid4().hex[:8]}"
        self.cycle_name = cycle_name
        self.current_index = 0
        self.notes: list[str] = []
        self.updated_at = datetime.now(UTC).isoformat()
        self._stage_status = {s: "pending" for s in STAGES}
        self._stage_status[STAGES[0]] = "in_progress"

    @property
    def current_stage(self) -> str:
        return STAGES[self.current_index]

    def snapshot(self) -> dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "cycle_name": self.cycle_name,
            "current_stage": self.current_stage,
            "stages": [{"stage": s, "status": self._stage_status[s]} for s in STAGES],
            "can_skip_to_management_review": self.current_stage
            not in ("management_review", "closed"),
            "notes": list(self.notes),
            "updated_at": self.updated_at,
            "scaffold": True,
        }

    def advance(self, *, note: str | None = None) -> dict[str, Any]:
        if self.current_stage == "closed":
            return self.snapshot()
        self._stage_status[self.current_stage] = "approved"
        if note:
            self.notes.append(note)
        if self.current_index < len(STAGES) - 1:
            self.current_index += 1
            if self.current_stage != "closed":
                self._stage_status[self.current_stage] = "in_progress"
            else:
                self._stage_status["closed"] = "closed"
        self.updated_at = datetime.now(UTC).isoformat()
        return self.snapshot()

    def skip_to_management_review(self, *, note: str | None = None) -> dict[str, Any]:
        """E2E-SOP-03 path: jump pending stages to skipped, land on management_review."""
        if self.current_stage in ("management_review", "closed"):
            return self.snapshot()
        target = STAGES.index("management_review")
        for i in range(self.current_index, target):
            self._stage_status[STAGES[i]] = "skipped"
        self.current_index = target
        self._stage_status["management_review"] = "in_progress"
        self.notes.append(note or "skip_to_management_review")
        self.updated_at = datetime.now(UTC).isoformat()
        return self.snapshot()


_DEFAULT = SopStageGateMachine()


def get_default_gate() -> SopStageGateMachine:
    return _DEFAULT


def reset_default_gate() -> SopStageGateMachine:
    global _DEFAULT
    _DEFAULT = SopStageGateMachine()
    return _DEFAULT
