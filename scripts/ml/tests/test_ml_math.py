#!/usr/bin/env python3
"""Tests for ML training math logic (no DB connection required)."""

from datetime import UTC, datetime, timedelta

from scripts.ml.train_supplier_reliability import compute_supplier_stats


def test_compute_supplier_stats_insufficient_samples():
    rows = [
        {"expected_date": datetime.now(UTC), "actual_date": datetime.now(UTC) + timedelta(days=1)},
    ]
    result = compute_supplier_stats(rows)
    assert result["insufficient"] is True
    assert result["sample_size"] == 1


def test_compute_supplier_stats_normal_distribution():
    rows = []
    base = datetime.now(UTC)
    for i in range(12):
        rows.append({
            "expected_date": base,
            "actual_date": base + timedelta(days=2 + (i % 3)),
        })
    result = compute_supplier_stats(rows)
    assert result["insufficient"] is False
    assert result["distribution_type"] == "normal"
    assert result["sample_size"] == 12
    assert "mu" in result
    assert "sigma" in result
    assert 0 < result["sigma"] < 2


def test_cycle_time_ratio():
    planned = [60, 120, 90]
    actual = [72, 132, 99]
    ratios = [a / p for a, p in zip(actual, planned)]
    avg_ratio = sum(ratios) / len(ratios)
    assert round(avg_ratio, 4) == 1.1333


def test_supplier_stats_negative_delays():
    rows = []
    base = datetime.now(UTC)
    for i in range(10):
        rows.append({
            "expected_date": base + timedelta(days=5),
            "actual_date": base + timedelta(days=3 + (i % 2)),
        })
    result = compute_supplier_stats(rows)
    assert result["mu"] < 0
    assert result["sample_size"] == 10
