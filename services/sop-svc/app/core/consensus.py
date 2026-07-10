from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConsensusWeights:
    sales: float = 0.30
    statistical: float = 0.40
    marketing: float = 0.20
    finance: float = 0.10


def calculate_consensus_qty(
    *,
    sales: float | None = None,
    statistical: float | None = None,
    marketing: float | None = None,
    finance: float | None = None,
    weights: ConsensusWeights | None = None,
) -> float:
    active_weights = weights or ConsensusWeights()
    inputs = (
        (sales, active_weights.sales),
        (statistical, active_weights.statistical),
        (marketing, active_weights.marketing),
        (finance, active_weights.finance),
    )
    available = [(float(qty), float(weight)) for qty, weight in inputs if qty is not None]
    total_weight = sum(weight for _, weight in available)
    if not available or total_weight <= 0:
        return 0.0
    return sum(qty * (weight / total_weight) for qty, weight in available)
