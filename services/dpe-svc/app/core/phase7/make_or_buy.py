"""Phase 7 §4.3 — Dynamic Make-or-Buy Decision Support.

Rule: make below the bottleneck-utilisation threshold; buy above it, because at the
constraint the opportunity cost of blocked capacity dominates the buy premium.
"""

from __future__ import annotations

from typing import Any


def analyze_make_or_buy(
    *,
    part: str = "SA-HVW",
    make_material_usd: float = 3_200.0,
    make_labour_usd: float = 850.0,
    make_overhead_usd: float = 420.0,
    make_hours: float = 6.0,
    make_quality_pct: float = 98.2,
    buy_price_usd: float = 5_100.0,
    buy_quality_pct: float = 96.5,
    current_utilisation_pct: float = 84.0,
    bottleneck_threshold_pct: float = 90.0,
    displaced_product: str = "DT100",
    displaced_margin_usd: float = 12_600.0,
) -> dict[str, Any]:
    make_cost = make_material_usd + make_labour_usd + make_overhead_usd
    buy_premium = round(buy_price_usd - make_cost, 2)
    premium_pct = round(buy_premium / make_cost * 100.0, 1) if make_cost else 0.0

    at_bottleneck = current_utilisation_pct > bottleneck_threshold_pct

    if not at_bottleneck:
        decision = "make"
        rationale = "Below threshold: lower cost, better quality, faster lead time."
        net_usd = -buy_premium  # cost avoided by making
    else:
        # At the bottleneck, making blocks higher-margin work.
        decision = "buy" if displaced_margin_usd > buy_premium else "make"
        rationale = (
            f"At the bottleneck, making {part} blocks a {displaced_product} unit worth "
            f"${displaced_margin_usd:,.0f} margin, which exceeds the buy premium "
            f"${buy_premium:,.0f}."
        )
        net_usd = round(displaced_margin_usd - buy_premium, 2)

    return {
        "part": part,
        "make": {
            "cost_usd": round(make_cost, 2),
            "hours": make_hours,
            "quality_pct": make_quality_pct,
        },
        "buy": {"price_usd": buy_price_usd, "quality_pct": buy_quality_pct},
        "buy_premium_usd": buy_premium,
        "buy_premium_pct": premium_pct,
        "current_utilisation_pct": current_utilisation_pct,
        "bottleneck_threshold_pct": bottleneck_threshold_pct,
        "at_bottleneck": at_bottleneck,
        "decision": decision,
        "rationale": rationale,
        "net_benefit_usd": net_usd,
        "rule": (
            f"Make when {'Winding'} utilisation < {bottleneck_threshold_pct:.0f}%; "
            f"buy when it exceeds {bottleneck_threshold_pct:.0f}% to free bottleneck capacity."
        ),
    }
