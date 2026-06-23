from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SopDemandBucket:
    period_start: datetime
    period_end: datetime
    product_family: str
    forecast_qty: float
    confidence_pct: float = 0.0


@dataclass
class SopCapacityBucket:
    period_start: datetime
    period_end: datetime
    work_center_group: str
    capacity_hours: float
    capacity_qty: float = 0.0


@dataclass
class SopGap:
    period_start: datetime
    period_end: datetime
    product_family: str
    demand_qty: float
    capacity_qty: float
    gap_qty: float
    gap_pct: float
    is_bottleneck: bool


@dataclass
class SopResult:
    plan_id: str = ""
    horizon_weeks: int = 52
    total_demand: float = 0.0
    total_capacity: float = 0.0
    total_gap: float = 0.0
    gap_pct: float = 0.0
    bottlenecks: list[SopGap] = field(default_factory=list)
    bucket_count: int = 0
    bottleneck_count: int = 0
    solve_time_ms: float = 0.0


def aggregate_to_weekly(
    demand_buckets: list[SopDemandBucket],
    capacity_buckets: list[SopCapacityBucket],
) -> tuple[dict[str, list[SopDemandBucket]], dict[str, list[SopCapacityBucket]]]:
    demand_by_week: dict[str, list[SopDemandBucket]] = {}
    for d in demand_buckets:
        week_key = d.period_start.strftime("%Y-W%W")
        demand_by_week.setdefault(week_key, []).append(d)

    capacity_by_week: dict[str, list[SopCapacityBucket]] = {}
    for c in capacity_buckets:
        week_key = c.period_start.strftime("%Y-W%W")
        capacity_by_week.setdefault(week_key, []).append(c)

    return demand_by_week, capacity_by_week


def compute_sop_gap(
    demand_buckets: list[SopDemandBucket],
    capacity_buckets: list[SopCapacityBucket],
    bottleneck_threshold_pct: float = 10.0,
) -> SopResult:
    import time
    start = time.monotonic()

    demand_by_week, cap_by_week = aggregate_to_weekly(demand_buckets, capacity_buckets)

    total_demand = 0.0
    total_capacity = 0.0
    bottlenecks: list[SopGap] = []

    all_weeks = sorted(set(list(demand_by_week.keys()) + list(cap_by_week.keys())))

    for week in all_weeks:
        week_demand = sum(d.forecast_qty for d in demand_by_week.get(week, []))
        week_cap = sum(c.capacity_qty if c.capacity_qty > 0 else c.capacity_hours for c in cap_by_week.get(week, []))

        total_demand += week_demand
        total_capacity += week_cap

        if week_demand > 0:
            gap = week_demand - week_cap
            gap_pct = (gap / week_demand) * 100.0 if week_demand > 0 else 0.0
            is_bottleneck = gap_pct >= bottleneck_threshold_pct

            if gap > 0 or is_bottleneck:
                period_start = None
                period_end = None
                product_family = ""
                for d in demand_by_week.get(week, []):
                    if period_start is None or d.period_start < period_start:
                        period_start = d.period_start
                    if period_end is None or d.period_end > period_end:
                        period_end = d.period_end
                    if not product_family:
                        product_family = d.product_family

                bottlenecks.append(SopGap(
                    period_start=period_start or datetime.min,
                    period_end=period_end or datetime.min,
                    product_family=product_family,
                    demand_qty=week_demand,
                    capacity_qty=week_cap,
                    gap_qty=round(gap, 2),
                    gap_pct=round(gap_pct, 2),
                    is_bottleneck=is_bottleneck,
                ))

    total_gap = total_demand - total_capacity
    gap_pct = (total_gap / total_demand * 100.0) if total_demand > 0 else 0.0

    elapsed = (time.monotonic() - start) * 1000.0

    return SopResult(
        horizon_weeks=len(all_weeks),
        total_demand=round(total_demand, 2),
        total_capacity=round(total_capacity, 2),
        total_gap=round(total_gap, 2),
        gap_pct=round(gap_pct, 2),
        bottlenecks=bottlenecks,
        bucket_count=len(all_weeks),
        bottleneck_count=len(bottlenecks),
        solve_time_ms=round(elapsed, 2),
    )