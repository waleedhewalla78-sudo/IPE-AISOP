"""Capacity auction — resolve WC slot conflicts with financial priority."""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class AuctionMO:
    id: str
    number: str
    margin: float
    margin_pct: float
    penalty_per_day: float
    order_value: float
    customer_priority: str
    days_to_deadline: int
    duration_days: float = 1.0


@dataclass
class AuctionEntry:
    mo_id: str
    mo_number: str
    margin: float
    penalty_per_day: float
    customer_priority: str
    days_to_deadline: int
    composite_score: float
    scores: dict[str, float] = field(default_factory=dict)


@dataclass
class AuctionResult:
    slot: dict[str, Any]
    winner: AuctionEntry
    reschedule_plan: list[dict[str, Any]]
    rationale: str


class CapacityAuction:
    WEIGHT_MARGIN = 0.25
    WEIGHT_PENALTY = 0.30
    WEIGHT_CUSTOMER_PRIORITY = 0.20
    WEIGHT_DEADLINE_TIGHTNESS = 0.25

    async def resolve_conflict(
        self,
        db: AsyncSession | None,
        tenant_id: str,
        competing_mos: list[dict[str, Any]] | list[AuctionMO],
        slot: dict[str, Any],
    ) -> dict[str, Any]:
        mos = [
            m
            if isinstance(m, AuctionMO)
            else AuctionMO(
                id=str(m.get("id") or m.get("mo_id")),
                number=str(m.get("number") or m.get("mo_number") or m.get("id")),
                margin=float(m.get("margin", 0)),
                margin_pct=float(m.get("margin_pct", m.get("margin", 20))),
                penalty_per_day=float(m.get("penalty_per_day", 0)),
                order_value=float(m.get("order_value", 10000) or 10000),
                customer_priority=str(m.get("customer_priority", "B")),
                days_to_deadline=int(m.get("days_to_deadline", 10)),
                duration_days=float(m.get("duration_days", 1)),
            )
            for m in competing_mos
        ]

        scores: list[AuctionEntry] = []
        for mo in mos:
            margin_score = self._score_margin(mo)
            penalty_score = self._score_penalty(mo)
            customer_score = self._score_customer(mo)
            deadline_score = self._score_deadline(mo, slot)
            composite = (
                self.WEIGHT_MARGIN * margin_score
                + self.WEIGHT_PENALTY * penalty_score
                + self.WEIGHT_CUSTOMER_PRIORITY * customer_score
                + self.WEIGHT_DEADLINE_TIGHTNESS * deadline_score
            )
            scores.append(
                AuctionEntry(
                    mo_id=mo.id,
                    mo_number=mo.number,
                    margin=mo.margin,
                    penalty_per_day=mo.penalty_per_day,
                    customer_priority=mo.customer_priority,
                    days_to_deadline=mo.days_to_deadline,
                    composite_score=round(composite, 2),
                    scores={
                        "margin": margin_score,
                        "penalty": penalty_score,
                        "customer": customer_score,
                        "deadline": deadline_score,
                    },
                )
            )

        scores.sort(key=lambda s: s.composite_score, reverse=True)
        winner = scores[0]
        losers = scores[1:]
        reschedule_plan = []
        for i, loser in enumerate(losers):
            delay_days = i + 1
            reschedule_plan.append(
                {
                    "mo_id": loser.mo_id,
                    "mo_number": loser.mo_number,
                    "new_slot": {"offset_days": delay_days},
                    "delay_days": delay_days,
                    "still_on_time": loser.days_to_deadline > delay_days,
                    "financial_impact": loser.penalty_per_day * delay_days
                    if loser.days_to_deadline <= delay_days
                    else 0,
                }
            )

        rationale = self._generate_rationale(winner, losers)
        result = AuctionResult(slot=slot, winner=winner, reschedule_plan=reschedule_plan, rationale=rationale)

        if db is not None:
            await self._log_auction(db, tenant_id, slot, winner, losers, reschedule_plan, rationale)

        return {
            "slot": slot,
            "winner": asdict(winner),
            "reschedule_plan": reschedule_plan,
            "rationale": rationale,
            "entries": [asdict(s) for s in scores],
        }

    def _score_margin(self, mo: AuctionMO) -> float:
        return min(mo.margin_pct / 50.0 * 100, 100)

    def _score_penalty(self, mo: AuctionMO) -> float:
        if mo.penalty_per_day == 0:
            return 20
        daily_penalty_pct = mo.penalty_per_day / max(mo.order_value, 1) * 100
        return min(daily_penalty_pct * 20, 100)

    def _score_customer(self, mo: AuctionMO) -> float:
        return {"A": 100, "B": 60, "C": 30}.get(mo.customer_priority.upper(), 50)

    def _score_deadline(self, mo: AuctionMO, slot: dict[str, Any]) -> float:
        duration = float(slot.get("duration_days", mo.duration_days))
        buffer = mo.days_to_deadline - duration
        if buffer <= 0:
            return 100
        if buffer <= 2:
            return 90
        if buffer <= 5:
            return 60
        if buffer <= 10:
            return 30
        return 10

    def _generate_rationale(self, winner: AuctionEntry, losers: list[AuctionEntry]) -> str:
        if not losers:
            return f"{winner.mo_number} assigned (no conflict)."
        return (
            f"{winner.mo_number} wins slot (score {winner.composite_score}). "
            f"{losers[0].mo_number} rescheduled — lower composite priority."
        )

    async def _log_auction(
        self,
        db: AsyncSession,
        tenant_id: str,
        slot: dict[str, Any],
        winner: AuctionEntry,
        losers: list[AuctionEntry],
        reschedule_plan: list[dict[str, Any]],
        rationale: str,
    ) -> None:
        import json

        await db.execute(
            text("""
                INSERT INTO cdm_capacity_auction_log (
                    tenant_id, work_centre_id, winner_mo_id, winner_score,
                    entries, reschedule_plan, rationale
                ) VALUES (
                    :tenant_id, :work_centre_id, :winner_mo_id, :winner_score,
                    CAST(:entries AS jsonb), CAST(:reschedule_plan AS jsonb), :rationale
                )
            """),
            {
                "tenant_id": UUID(tenant_id),
                "work_centre_id": UUID(slot["work_centre_id"])
                if slot.get("work_centre_id") and _is_uuid(str(slot["work_centre_id"]))
                else None,
                "winner_mo_id": UUID(winner.mo_id) if _is_uuid(winner.mo_id) else None,
                "winner_score": winner.composite_score,
                "entries": json.dumps([asdict(winner)] + [asdict(l) for l in losers]),
                "reschedule_plan": json.dumps(reschedule_plan),
                "rationale": rationale,
            },
        )


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except ValueError:
        return False
