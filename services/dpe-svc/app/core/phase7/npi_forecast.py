"""Phase 7 §3.3 — New Product Introduction demand forecasting.

Three methods composited: analogy-based ramp, cannibalization, and market sizing.
"""

from __future__ import annotations

from typing import Any

# DT100 first 12 months (analogy reference ramp), normalised to mature demand.
_DEFAULT_REF_RAMP = [8, 10, 12, 15, 18, 20, 22, 20, 22, 24, 25, 25]


def forecast_npi(
    *,
    product: str = "DT100-V2",
    reference_product: str = "DT100",
    reference_ramp: list[float] | None = None,
    mature_demand: float = 15.0,
    cannibalization_pct: float = 30.0,
    reference_current_demand: float = 24.0,
    net_new_units: float = 5.0,
    market_total_annual: float = 500.0,
    market_share_pct: float = 15.0,
    addressable_pct: float = 60.0,
    months: int = 12,
) -> dict[str, Any]:
    reference_ramp = reference_ramp or _DEFAULT_REF_RAMP
    ref_mature = max(reference_ramp) or 1.0
    ramp_ratio = [round(v / ref_mature, 3) for v in reference_ramp]

    # Method 1 — analogy ramp scaled to this product's mature demand.
    analogy = [round(mature_demand * r, 1) for r in ramp_ratio[:months]]

    # Method 2 — cannibalization.
    cannibalized = round(reference_current_demand * cannibalization_pct / 100.0, 1)
    ref_after = round(reference_current_demand - cannibalized, 1)
    method2_forecast = round(cannibalized + net_new_units, 1)

    # Method 3 — market sizing.
    share_units_year = market_total_annual * market_share_pct / 100.0
    addressable_month = round(share_units_year * addressable_pct / 100.0 / 12.0, 2)

    # Composite: blend analogy ramp with cannibalization steady-state target.
    composite: list[dict[str, Any]] = []
    for m in range(1, months + 1):
        analogy_m = analogy[m - 1] if m - 1 < len(analogy) else analogy[-1]
        # Cannibalization of the reference product begins at month 3.
        ref_cannibalized = -cannibalized if m >= 3 else 0.0
        composite.append(
            {
                "month": m,
                "npi_forecast_units": analogy_m,
                "reference_cannibalization_units": ref_cannibalized,
                "confidence": "low" if m <= 3 else "medium",
            }
        )

    return {
        "product": product,
        "reference_product": reference_product,
        "methods": {
            "analogy": {
                "ramp_ratio": ramp_ratio[:months],
                "month_1_units": analogy[0] if analogy else 0.0,
                "confidence": "low",
            },
            "cannibalization": {
                "cannibalized_units": cannibalized,
                "reference_after_units": ref_after,
                "net_new_units": net_new_units,
                "forecast_units": method2_forecast,
                "confidence": "medium",
            },
            "market_sizing": {
                "market_total_annual": market_total_annual,
                "share_units_year": share_units_year,
                "addressable_units_month": addressable_month,
                "confidence": "low",
            },
        },
        "composite_forecast": composite,
        "planning_recommendation": [
            "Pre-position materials for first 3 months buffer",
            f"MPS includes {product} from month 1",
            f"Reduce {reference_product} MPS by {cannibalized:.0f} units starting month 3",
            "Review forecast vs actuals monthly — adjust aggressively",
        ],
        "risk": (
            f"If adoption is slower, excess {product} material — but it is common with "
            f"{reference_product}, so no obsolescence risk."
        ),
    }
