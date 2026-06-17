"""
Unit test for shadow_mode_comparison.py comparison logic.

Verifies that the OTD computation and report generation logic
executes correctly with mocked historical data.
"""

import json
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import validation.shadow_mode_comparison as smc


def test_compute_historical_otd_all_on_time() -> None:
    mos = [
        {"historical_on_time": True, "id": str(uuid.uuid4())},
        {"historical_on_time": True, "id": str(uuid.uuid4())},
        {"historical_on_time": True, "id": str(uuid.uuid4())},
    ]
    otd = smc._compute_historical_otd(mos)
    assert otd == 100.0


def test_compute_historical_otd_mixed() -> None:
    mos = [
        {"historical_on_time": True, "id": str(uuid.uuid4())},
        {"historical_on_time": False, "id": str(uuid.uuid4())},
        {"historical_on_time": True, "id": str(uuid.uuid4())},
        {"historical_on_time": False, "id": str(uuid.uuid4())},
    ]
    otd = smc._compute_historical_otd(mos)
    assert otd == 50.0


def test_compute_historical_otd_empty() -> None:
    assert smc._compute_historical_otd([]) == 0.0


def test_compute_ipe_otd() -> None:
    results = [
        {"ipe_on_time": True, "mo_id": "1"},
        {"ipe_on_time": False, "mo_id": "2"},
        {"ipe_on_time": True, "mo_id": "3"},
    ]
    otd = smc._compute_ipe_otd(results)
    assert otd == pytest.approx(66.6667, rel=1e-3)


def test_compute_ipe_otd_empty() -> None:
    assert smc._compute_ipe_otd([]) == 0.0


def test_generate_report_pass() -> None:
    results = [{"ipe_on_time": True, "mo_id": "1"} for _ in range(10)]
    report = smc._generate_report(results, historical_otd=80.0, ipe_otd=92.5)
    assert report["ipe_predicted_otd"] == 92.5
    assert report["historical_actual_otd"] == 80.0
    assert report["improvement_delta"] == 12.5
    assert report["pass"] is True
    assert report["total_mos_evaluated"] == 10


def test_generate_report_fail() -> None:
    results = [{"ipe_on_time": False, "mo_id": "1"} for _ in range(10)]
    report = smc._generate_report(results, historical_otd=80.0, ipe_otd=75.0)
    assert report["improvement_delta"] == -5.0
    assert report["pass"] is False


def test_generate_historical_mos_produces_correct_count() -> None:
    tenant_id = str(uuid.uuid4())
    mos = smc._generate_historical_mos(50, tenant_id, seed=1)
    assert len(mos) == 50
    assert all(m["tenant_id"] == tenant_id for m in mos)
    assert all(m["status"] == "completed" for m in mos)
    assert all("historical_on_time" in m for m in mos)


def test_full_pipeline_mocked() -> None:
    """End-to-end test with heuristic fallback (no real services needed)."""
    tenant_id = str(uuid.uuid4())
    mos = smc._generate_historical_mos(20, tenant_id, seed=42)
    historical_otd = smc._compute_historical_otd(mos)

    import asyncio

    results = asyncio.run(
        smc._run_evaluation(
            mos,
            dpe_url="http://localhost:9999",
            mat_url="http://localhost:9999",
            cap_url="http://localhost:9999",
        )
    )
    assert len(results) == 20

    ipe_otd = smc._compute_ipe_otd(results)
    report = smc._generate_report(results, historical_otd, ipe_otd)

    # Verify report structure
    assert "ipe_predicted_otd" in report
    assert "historical_actual_otd" in report
    assert "improvement_delta" in report
    assert "total_mos_evaluated" in report
    assert "pass" in report
    assert report["total_mos_evaluated"] == 20

    # Verify JSON-serializable
    json.dumps(report)
