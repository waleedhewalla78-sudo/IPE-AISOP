"""Phase 7 §3.2 — Demand Collaboration Workflow.

Structured multi-stakeholder consensus: statistical baseline + Sales/Marketing/
Finance inputs, weighted by role weight x credibility, with disagreement flags and
bias tracking that decays the weight of persistently biased contributors.
"""

from __future__ import annotations

from typing import Any

_DEFAULT_WEIGHTS = {"statistical": 0.35, "sales": 0.30, "marketing": 0.20, "finance": 0.15}


def build_consensus(
    *,
    product: str = "FG-DT100",
    period: str = "October",
    statistical: float = 23.0,
    inputs: list[dict[str, Any]] | None = None,
    weights: dict[str, float] | None = None,
    disagreement_threshold_pct: float = 15.0,
) -> dict[str, Any]:
    """Compute a weighted consensus.

    ``inputs`` items: {source, value, rationale?, credibility?(0-1), bias_history_pct?}.
    Bias tracking: a source with persistent bias > threshold gets its weight decayed
    for the next cycle.
    """

    weights = dict(weights or _DEFAULT_WEIGHTS)
    inputs = inputs or [
        {
            "source": "sales",
            "value": 28,
            "rationale": "Egyptian Electric expanding order program",
            "credibility": 0.85,
            "bias_history_pct": 15.0,
        },
        {
            "source": "marketing",
            "value": 25,
            "rationale": "October promotion expected +4 units",
            "credibility": 1.0,
            "bias_history_pct": 4.0,
        },
        {
            "source": "finance",
            "value": 24,
            "rationale": "AOP target for H2",
            "credibility": 1.0,
            "bias_history_pct": 2.0,
        },
    ]

    contributions: list[dict[str, Any]] = []
    weighted_sum = 0.0
    nominal_weight_total = 0.0

    stat_w = weights.get("statistical", 0.35)
    weighted_sum += statistical * stat_w
    nominal_weight_total += stat_w
    contributions.append(
        {
            "source": "statistical",
            "value": statistical,
            "weight": stat_w,
            "credibility": 1.0,
            "contribution": round(statistical * stat_w, 3),
        }
    )

    for item in inputs:
        src = item["source"]
        val = float(item["value"])
        w = weights.get(src, 0.10)
        cred = float(item.get("credibility", 1.0))
        weighted_sum += val * w * cred
        nominal_weight_total += w
        contributions.append(
            {
                "source": src,
                "value": val,
                "weight": w,
                "credibility": cred,
                "rationale": item.get("rationale"),
                "contribution": round(val * w * cred, 3),
            }
        )

    # Normalise by the NOMINAL weight total (so partial input sets still work);
    # credibility discounts a contributor's pull without re-normalising it away —
    # this matches the documented consensus (full 4-source example ≈ 23.8).
    consensus_raw = weighted_sum / nominal_weight_total if nominal_weight_total else statistical
    consensus = round(consensus_raw)

    disagreements: list[dict[str, Any]] = []
    bias_adjustments: list[dict[str, Any]] = []
    for item in inputs:
        val = float(item["value"])
        dev_pct = abs(val - consensus_raw) / consensus_raw * 100.0 if consensus_raw else 0.0
        if dev_pct > disagreement_threshold_pct:
            disagreements.append(
                {
                    "source": item["source"],
                    "value": val,
                    "deviation_pct": round(dev_pct, 1),
                    "action": "Discuss in demand review; provide order evidence or adjust.",
                }
            )
        bias = float(item.get("bias_history_pct", 0.0))
        if bias >= disagreement_threshold_pct:
            old_w = weights.get(item["source"], 0.10)
            new_w = round(old_w - 0.05, 3)
            bias_adjustments.append(
                {
                    "source": item["source"],
                    "bias_history_pct": bias,
                    "weight_from": old_w,
                    "weight_to": max(new_w, 0.05),
                    "note": "Persistent bias — weight decayed next cycle until accuracy improves.",
                }
            )

    return {
        "product": product,
        "period": period,
        "statistical_baseline": statistical,
        "contributions": contributions,
        "consensus_raw": round(consensus_raw, 2),
        "consensus_units": consensus,
        "disagreement_flags": disagreements,
        "bias_tracking": bias_adjustments,
        "status": "needs_review" if disagreements else "agreed",
    }
