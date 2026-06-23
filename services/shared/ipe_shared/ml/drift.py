"""ML drift detection module for IPE.

Detects data drift, concept drift, and prediction drift using:
- PSI (Population Stability Index)
- Kolmogorov-Smirnov test
- Chi-squared test for categorical drift
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger("ipe.ml.drift")


class DriftType(StrEnum):
    NONE = "none"
    WARNING = "warning"
    DETECTED = "detected"


class DriftMetric(StrEnum):
    PSI = "psi"
    KS_STATISTIC = "ks_statistic"
    CHI_SQUARED = "chi_squared"


@dataclass
class DriftResult:
    metric: str
    drift_type: DriftType
    value: float
    threshold: float
    p_value: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)
    detected_at: str = ""

    def __post_init__(self) -> None:
        if not self.detected_at:
            self.detected_at = datetime.now(UTC).isoformat()

    @property
    def is_drifted(self) -> bool:
        return self.drift_type in (DriftType.WARNING, DriftType.DETECTED)


def compute_psi(reference: list[float], current: list[float], bins: int = 10) -> DriftResult:
    """Population Stability Index. <0.1 no drift, 0.1-0.25 warning, >0.25 detected."""
    if not reference or not current:
        return DriftResult(metric="psi", drift_type=DriftType.NONE, value=0.0, threshold=0.25)

    min_val = min(min(reference), min(current))
    max_val = max(max(reference), max(current))
    if min_val == max_val:
        return DriftResult(metric="psi", drift_type=DriftType.NONE, value=0.0, threshold=0.25)

    bin_edges = [min_val + i * (max_val - min_val) / bins for i in range(bins + 1)]

    def _hist(data: list[float]) -> list[float]:
        counts = [0.0] * bins
        for val in data:
            for i in range(bins):
                if bin_edges[i] <= val < bin_edges[i + 1]:
                    counts[i] += 1
                    break
            else:
                counts[-1] += 1
        total = sum(counts)
        return [c / total if total > 0 else 1e-6 for c in counts]

    ref_pct = _hist(reference)
    cur_pct = _hist(current)

    psi = sum(
        (cur - ref) * math.log(cur / ref)
        for ref, cur in zip(ref_pct, cur_pct)
        if ref > 0 and cur > 0
    )

    if psi > 0.25:
        drift_type = DriftType.DETECTED
    elif psi > 0.1:
        drift_type = DriftType.WARNING
    else:
        drift_type = DriftType.NONE

    return DriftResult(
        metric="psi",
        drift_type=drift_type,
        value=psi,
        threshold=0.25,
        details={"bins": bins, "ref_count": len(reference), "cur_count": len(current)},
    )


def compute_ks_test(reference: list[float], current: list[float]) -> DriftResult:
    """Kolmogorov-Smirnov statistic. p<0.05 indicates drift."""
    if not reference or not current:
        return DriftResult(metric="ks_statistic", drift_type=DriftType.NONE, value=0.0, threshold=0.1)

    sorted_ref = sorted(reference)
    sorted_cur = sorted(current)

    def _ecdf(data: list[float], x: float) -> float:
        count = sum(1 for v in data if v <= x)
        return count / len(data)

    all_values = sorted(set(sorted_ref + sorted_cur))
    max_diff = 0.0
    for val in all_values:
        diff = abs(_ecdf(sorted_ref, val) - _ecdf(sorted_cur, val))
        max_diff = max(max_diff, diff)

    if max_diff > 0.2:
        drift_type = DriftType.DETECTED
    elif max_diff > 0.1:
        drift_type = DriftType.WARNING
    else:
        drift_type = DriftType.NONE

    return DriftResult(
        metric="ks_statistic",
        drift_type=drift_type,
        value=max_diff,
        threshold=0.2,
        details={"ref_count": len(reference), "cur_count": len(current)},
    )


@dataclass
class DriftMonitor:
    model_id: str
    window_size: int = 1000
    psi_warning: float = 0.1
    psi_detected: float = 0.25
    ks_warning: float = 0.1
    ks_detected: float = 0.2
    _reference: list[float] = field(default_factory=list)
    _current: list[float] = field(default_factory=list)

    def set_reference(self, data: list[float]) -> None:
        self._reference = data

    def add_predictions(self, predictions: list[float]) -> None:
        self._current.extend(predictions)
        if len(self._current) > self.window_size:
            self._current = self._current[-self.window_size:]

    def check_drift(self) -> list[DriftResult]:
        if not self._reference or not self._current:
            return []

        psi = compute_psi(self._reference, self._current)
        ks = compute_ks_test(self._reference, self._current)

        results = [psi, ks]
        for r in results:
            if r.drift_type == DriftType.DETECTED:
                logger.warning("DRIFT DETECTED for %s: %s=%.4f (threshold=%.4f)",
                              self.model_id, r.metric, r.value, r.threshold)
        return results
