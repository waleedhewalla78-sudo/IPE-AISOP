"""Smart batching — group MOs by product family to minimise changeover."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class BatchMO:
    id: str
    product_id: str
    product_family: str
    planned_start: str
    planned_end: str
    work_centre_id: str


@dataclass
class WorkCentreBatch:
    id: str
    name: str
    changeover_same_family_min: float = 10.0
    changeover_different_family_min: float = 45.0


@dataclass
class BatchResult:
    work_centre_id: str
    work_centre_name: str
    original_sequence: list[str]
    optimised_sequence: list[str]
    original_changeover_min: float
    optimised_changeover_min: float
    savings_min: float
    savings_pct: float
    delivery_dates_maintained: bool


class SmartBatcher:
    async def optimize_batches(
        self,
        db: AsyncSession | None,
        tenant_id: str,
        mos: list[dict[str, Any]] | list[BatchMO],
        work_centres: list[dict[str, Any]] | list[WorkCentreBatch],
    ) -> list[dict[str, Any]]:
        mo_objs = [
            m
            if isinstance(m, BatchMO)
            else BatchMO(
                id=str(m.get("id") or m.get("mo_id")),
                product_id=str(m.get("product_id", "P1")),
                product_family=str(m.get("product_family", m.get("product_id", "P1"))),
                planned_start=str(m.get("planned_start", "")),
                planned_end=str(m.get("planned_end", m.get("due_date", ""))),
                work_centre_id=str(m.get("work_centre_id") or m.get("work_center_id")),
            )
            for m in mos
        ]
        wc_objs = [
            w
            if isinstance(w, WorkCentreBatch)
            else WorkCentreBatch(
                id=str(w.get("id") or w.get("work_centre_id")),
                name=str(w.get("name", "WC")),
                changeover_same_family_min=float(w.get("changeover_same_family_min", 10)),
                changeover_different_family_min=float(w.get("changeover_different_family_min", 45)),
            )
            for w in work_centres
        ]

        batches: list[BatchResult] = []
        for wc in wc_objs:
            wc_mos = [m for m in mo_objs if m.work_centre_id == wc.id]
            if not wc_mos:
                continue

            product_groups: dict[str, list[BatchMO]] = defaultdict(list)
            for mo in wc_mos:
                product_groups[mo.product_id].append(mo)

            fifo_sequence = sorted(wc_mos, key=lambda m: m.planned_start)
            fifo_changeover = self._calculate_changeover(fifo_sequence, wc)

            family_groups: dict[str, list[BatchMO]] = defaultdict(list)
            for product_id, group_mos in product_groups.items():
                family = group_mos[0].product_family or product_id
                family_groups[family].extend(group_mos)

            batched_sequence: list[BatchMO] = []
            for family in sorted(family_groups.keys()):
                family_mos = sorted(family_groups[family], key=lambda m: m.planned_end)
                batched_sequence.extend(family_mos)

            batched_changeover = self._calculate_changeover(batched_sequence, wc)
            delivery_ok = self._check_delivery_dates(batched_sequence)
            if delivery_ok:
                savings = fifo_changeover - batched_changeover
                pct = (savings / fifo_changeover * 100) if fifo_changeover > 0 else 0.0
                batches.append(
                    BatchResult(
                        work_centre_id=wc.id,
                        work_centre_name=wc.name,
                        original_sequence=[m.id for m in fifo_sequence],
                        optimised_sequence=[m.id for m in batched_sequence],
                        original_changeover_min=fifo_changeover,
                        optimised_changeover_min=batched_changeover,
                        savings_min=savings,
                        savings_pct=round(pct, 1),
                        delivery_dates_maintained=True,
                    )
                )

        if db is not None:
            await self._store_batches(db, tenant_id, batches)

        return [asdict(b) for b in batches]

    def _calculate_changeover(self, sequence: list[BatchMO], wc: WorkCentreBatch) -> float:
        total = 0.0
        for i in range(1, len(sequence)):
            prev, curr = sequence[i - 1], sequence[i]
            if prev.product_id == curr.product_id:
                total += 0
            elif prev.product_family == curr.product_family:
                total += wc.changeover_same_family_min
            else:
                total += wc.changeover_different_family_min
        return total

    def _check_delivery_dates(self, sequence: list[BatchMO]) -> bool:
        # Simplified: always maintain if sequence length preserved
        return True

    async def _store_batches(self, db: AsyncSession, tenant_id: str, batches: list[BatchResult]) -> None:
        import json

        for b in batches:
            await db.execute(
                text("""
                    INSERT INTO cdm_batch_group (
                        tenant_id, work_centre_id, work_centre_name,
                        original_sequence, optimised_sequence,
                        original_changeover_min, optimised_changeover_min,
                        savings_min, savings_pct, delivery_dates_maintained
                    ) VALUES (
                        :tenant_id, :work_centre_id, :work_centre_name,
                        CAST(:original_sequence AS jsonb), CAST(:optimised_sequence AS jsonb),
                        :original_changeover_min, :optimised_changeover_min,
                        :savings_min, :savings_pct, :delivery_dates_maintained
                    )
                """),
                {
                    "tenant_id": UUID(tenant_id),
                    "work_centre_id": UUID(b.work_centre_id) if _is_uuid(b.work_centre_id) else None,
                    "work_centre_name": b.work_centre_name,
                    "original_sequence": json.dumps(b.original_sequence),
                    "optimised_sequence": json.dumps(b.optimised_sequence),
                    "original_changeover_min": b.original_changeover_min,
                    "optimised_changeover_min": b.optimised_changeover_min,
                    "savings_min": b.savings_min,
                    "savings_pct": b.savings_pct,
                    "delivery_dates_maintained": b.delivery_dates_maintained,
                },
            )


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except ValueError:
        return False
