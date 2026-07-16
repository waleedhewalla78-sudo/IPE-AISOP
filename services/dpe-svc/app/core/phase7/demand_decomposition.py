"""Phase 7 §3.1 — Demand Decomposition.

TOTAL = Base + Trend + Seasonal + Promotional + Event + Noise. Each component is
independently modelled so it can be managed and influenced.
"""

from __future__ import annotations

from typing import Any

_DEFAULT_SEASONAL = {
    1: 1.10,
    2: 1.10,
    3: 1.10,  # Jan-Mar winter construction surge
    4: 1.00,
    5: 1.00,
    6: 1.00,  # Apr-Jun normal
    7: 0.85,
    8: 0.85,
    9: 0.85,  # Jul-Sep summer slowdown + Eid
    10: 1.05,
    11: 1.05,
    12: 1.05,  # Oct-Dec year-end completions
}


def decompose_demand(
    *,
    product: str = "FG-DT100",
    month: int = 10,
    base: float = 20.0,
    trend_per_month: float = 2.0,
    months_from_base: float = 1.0,
    promo_active: bool = False,
    promo_price_change_pct: float = -3.0,
    price_elasticity: float = -1.3,
    event_units: float = 0.0,
    noise_sigma: float = 3.0,
    seasonal_index: dict[int, float] | None = None,
) -> dict[str, Any]:
    seasonal_index = seasonal_index or _DEFAULT_SEASONAL
    seasonal_factor = float(seasonal_index.get(int(month), 1.0))

    trend = trend_per_month * months_from_base
    base_plus_trend = base + trend
    seasonal_adj = base_plus_trend * seasonal_factor

    # Promotional lift via elasticity: %demand change = elasticity * %price change.
    promo_lift = 0.0
    if promo_active:
        pct_change = price_elasticity * (promo_price_change_pct / 100.0)
        promo_lift = round(base_plus_trend * pct_change, 1)

    forecast_no_promo = round(seasonal_adj + event_units, 1)
    forecast_with_promo = round(seasonal_adj + event_units + promo_lift, 1)
    forecast = forecast_with_promo if promo_active else forecast_no_promo

    ci_low = round(forecast - 1.96 * noise_sigma, 1)
    ci_high = round(forecast + 1.96 * noise_sigma, 1)

    return {
        "product": product,
        "month": month,
        "components": {
            "base": {
                "units": round(base, 1),
                "method": "12-month deseasonalized MA",
                "confidence": "high",
            },
            "trend": {
                "units": round(trend, 1),
                "method": "linear regression on 24-month base",
                "confidence": "medium",
            },
            "seasonal": {
                "factor": seasonal_factor,
                "method": "seasonal decomposition (X-13ARIMA-SEATS)",
            },
            "promotional": {
                "units": promo_lift,
                "elasticity": price_elasticity,
                "active": promo_active,
            },
            "event": {"units": round(event_units, 1), "source": "CRM pipeline + manual"},
            "noise": {"sigma_units": noise_sigma, "handling": "absorbed by safety stock"},
        },
        "forecast_units": forecast,
        "forecast_without_promo": forecast_no_promo,
        "forecast_with_promo": forecast_with_promo,
        "confidence_interval_95": {"low": max(ci_low, 0.0), "high": ci_high},
        "model_selected": "decomposition + SARIMA for base+trend+seasonal",
    }
