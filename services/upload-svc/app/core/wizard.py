"""5-phase data onboarding wizard state."""

from __future__ import annotations

from typing import Any

from app.core.validator import FILE_SCHEMAS

PHASES = [
    {
        "phase": 1,
        "name": "Master Data",
        "name_ar": "البيانات الأساسية",
        "files": ["product_master", "customer_master", "supplier_master", "work_centre_master"],
        "agents": ["A2", "A4"],
    },
    {
        "phase": 2,
        "name": "Product Structure",
        "name_ar": "هيكل المنتجات",
        "files": ["bom", "routing"],
        "agents": ["A4"],
    },
    {
        "phase": 3,
        "name": "Planning Parameters",
        "name_ar": "معاملات التخطيط",
        "files": ["capacity_calendar", "lead_time", "cost_data"],
        "agents": ["A2", "A3", "A5"],
    },
    {
        "phase": 4,
        "name": "Current State",
        "name_ar": "الحالة الحالية",
        "files": ["inventory", "production_orders", "sales_orders", "purchase_orders"],
        "agents": ["A1", "A2", "A3", "A4"],
    },
    {
        "phase": 5,
        "name": "Historical Data",
        "name_ar": "البيانات التاريخية",
        "files": ["historical_otd"],
        "agents": ["A6", "A7"],
    },
]


class OnboardingWizard:
    def __init__(self) -> None:
        # tenant_id -> {phase_number: {file_type: status}}
        self._state: dict[str, dict[str, Any]] = {}

    def _ensure(self, tenant_id: str) -> dict[str, Any]:
        if tenant_id not in self._state:
            self._state[tenant_id] = {
                "current_phase": 1,
                "completed_files": set(),
                "agents_activated": [],
            }
        return self._state[tenant_id]

    def status(self, tenant_id: str) -> dict[str, Any]:
        st = self._ensure(tenant_id)
        completed = st["completed_files"]
        phases_out = []
        for p in PHASES:
            uploaded = [f for f in p["files"] if f in completed]
            if p["phase"] < st["current_phase"]:
                status = "complete"
            elif p["phase"] == st["current_phase"]:
                status = "complete" if len(uploaded) == len(p["files"]) else "in_progress"
            else:
                status = "locked"
            phases_out.append(
                {
                    **{k: v for k, v in p.items() if k != "agents"},
                    "status": status,
                    "files_uploaded": len(uploaded),
                    "files_remaining": len(p["files"]) - len(uploaded),
                    "unlock_message": None
                    if status != "locked"
                    else f"Complete Phase {p['phase'] - 1} first",
                }
            )
        all_agents = ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]
        activated = list(st["agents_activated"])
        return {
            "current_phase": st["current_phase"],
            "phases": phases_out,
            "agents_activated": activated,
            "agents_pending": [a for a in all_agents if a not in activated],
        }

    def record_upload(self, tenant_id: str, file_type: str) -> None:
        st = self._ensure(tenant_id)
        if file_type in FILE_SCHEMAS:
            st["completed_files"].add(file_type)

    def complete_phase(self, tenant_id: str, phase_number: int) -> dict[str, Any]:
        st = self._ensure(tenant_id)
        phase = next((p for p in PHASES if p["phase"] == phase_number), None)
        if not phase:
            raise ValueError(f"Invalid phase {phase_number}")
        if phase_number > st["current_phase"]:
            raise ValueError("Phase is locked")
        for f in phase["files"]:
            st["completed_files"].add(f)
        newly = [a for a in phase["agents"] if a not in st["agents_activated"]]
        st["agents_activated"].extend(newly)
        if phase_number >= st["current_phase"] and phase_number < 5:
            st["current_phase"] = phase_number + 1
        elif phase_number == 5:
            st["current_phase"] = 5
        return {
            "phase_completed": phase_number,
            "agents_newly_activated": newly,
            "next_phase": st["current_phase"] if phase_number < 5 else None,
            "message": (
                f"Phase {phase_number} complete. "
                + (
                    f"Upload planning parameters in Phase {st['current_phase']}."
                    if phase_number < 5
                    else "All 14 files loaded. IPE agents are now active."
                )
            ),
        }


wizard_store = OnboardingWizard()
