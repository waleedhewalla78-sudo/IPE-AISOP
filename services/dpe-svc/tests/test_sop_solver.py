from datetime import UTC, datetime, timedelta

from app.core.sop_solver import (
    SopCapacityBucket,
    SopDemandBucket,
    SopResult,
    aggregate_to_weekly,
    compute_sop_gap,
)


def _make_demand(qty: float, family: str = "A", week: int = 0) -> SopDemandBucket:
    base = datetime(2026, 1, 6, tzinfo=UTC)
    return SopDemandBucket(
        period_start=base + timedelta(weeks=week),
        period_end=base + timedelta(weeks=week + 1),
        product_family=family,
        forecast_qty=qty,
        confidence_pct=0.8,
    )


def _make_cap(qty: float, group: str = "WC-A", week: int = 0) -> SopCapacityBucket:
    base = datetime(2026, 1, 6, tzinfo=UTC)
    return SopCapacityBucket(
        period_start=base + timedelta(weeks=week),
        period_end=base + timedelta(weeks=week + 1),
        work_center_group=group,
        capacity_hours=qty,
        capacity_qty=qty,
    )


class TestAggregateToWeekly:
    def test_single_demand_bucket(self):
        d = [_make_demand(100)]
        result_d, result_c = aggregate_to_weekly(d, [])
        assert len(result_d) == 1

    def test_multi_week_aggregation(self):
        d = [_make_demand(100, week=i) for i in range(4)]
        result_d, result_c = aggregate_to_weekly(d, [])
        assert len(result_d) == 4

    def test_bucket_key_format(self):
        d = [_make_demand(100)]
        result_d, _ = aggregate_to_weekly(d, [])
        keys = list(result_d.keys())
        assert keys[0].startswith("2026-W")


class TestComputeSopGap:
    def test_balanced_demand_capacity(self):
        demand = [_make_demand(100, week=i) for i in range(4)]
        capacity = [_make_cap(100, week=i) for i in range(4)]
        result = compute_sop_gap(demand, capacity)
        assert result.total_demand == 400.0
        assert result.total_capacity == 400.0
        assert result.total_gap == 0.0
        assert result.gap_pct <= 0.01

    def test_demand_exceeds_capacity(self):
        demand = [_make_demand(120, week=i) for i in range(4)]
        capacity = [_make_cap(100, week=i) for i in range(4)]
        result = compute_sop_gap(demand, capacity)
        assert result.total_demand == 480.0
        assert result.total_gap > 0

    def test_bottleneck_detection(self):
        demand = [_make_demand(150, week=0)]
        capacity = [_make_cap(100, week=0)]
        result = compute_sop_gap(demand, capacity, bottleneck_threshold_pct=10.0)
        assert result.bottleneck_count >= 1
        assert any(b.is_bottleneck for b in result.bottlenecks)

    def test_empty_inputs(self):
        result = compute_sop_gap([], [])
        assert result.total_demand == 0.0
        assert result.bottleneck_count == 0

    def test_solve_time_within_budget(self):
        demand = [_make_demand(100 + i * 10, week=i) for i in range(52)]
        capacity = [_make_cap(100, week=i) for i in range(52)]
        result = compute_sop_gap(demand, capacity)
        assert result.solve_time_ms < 10000

    def test_below_threshold_not_bottleneck(self):
        demand = [_make_demand(105, week=0)]
        capacity = [_make_cap(100, week=0)]
        result = compute_sop_gap(demand, capacity, bottleneck_threshold_pct=20.0)
        for b in result.bottlenecks:
            if b.gap_pct < 20.0:
                assert not b.is_bottleneck

    def test_gap_pct_calculation(self):
        demand = [_make_demand(200, week=0)]
        capacity = [_make_cap(100, week=0)]
        result = compute_sop_gap(demand, capacity)
        assert result.gap_pct > 0

    def test_single_week_gap(self):
        demand = [_make_demand(500, week=10)]
        capacity = [_make_cap(300, week=10)]
        result = compute_sop_gap(demand, capacity)
        assert len(result.bottlenecks) >= 1
        assert result.bottlenecks[0].gap_qty == 200.0