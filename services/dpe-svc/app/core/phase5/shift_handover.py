"""B1.3 Shift handover summary."""

from __future__ import annotations

from typing import Any


def build_shift_handover(
    *,
    from_shift: str,
    to_shift: str,
    completed_mos: list[str],
    in_progress: list[dict[str, Any]],
    open_issues: list[str],
    quality_holds: list[str] | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    quality_holds = quality_holds or []
    summary = (
        f"Shift {from_shift} closing → {to_shift}. "
        f"Completed {len(completed_mos)} MOs; {len(in_progress)} still running; "
        f"{len(open_issues)} open issues; {len(quality_holds)} quality holds."
    )
    return {
        "from_shift": from_shift,
        "to_shift": to_shift,
        "ai_summary": notes or summary,
        "completed_mos": completed_mos,
        "in_progress": in_progress,
        "open_issues": open_issues,
        "quality_holds": quality_holds,
        "acknowledge_required": True,
    }
