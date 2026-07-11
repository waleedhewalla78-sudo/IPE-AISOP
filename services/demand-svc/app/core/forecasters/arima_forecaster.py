"""ARIMA-family forecasters with SES fallbacks and time-budget guards."""

from __future__ import annotations

import time
import warnings
from statistics import pstdev
from typing import Any

from app.core.forecaster import forecast_series as ses_forecast_series


def _fallback(history: list[float], periods: int) -> list[dict[str, float]]:
    return ses_forecast_series(history, periods)


def _bands(history: list[float], value: float) -> dict[str, float]:
    spread = pstdev(history) if len(history) > 1 else max(abs(value) * 0.1, 1.0)
    return {
        "value": round(float(value), 4),
        "lower": round(max(0.0, float(value) - 1.96 * spread), 4),
        "upper": round(float(value) + 1.96 * spread, 4),
    }


class ARIMAForecaster:
    """Auto-order ARIMA over a deliberately small search space.

    ``predict`` accepts an optional ``deadline`` (monotonic timestamp).  When
    supplied, each inner grid iteration checks whether the wall-clock budget has
    been exhausted and returns the best fit found so far rather than continuing.
    If no order converged before the deadline the method raises ``ValueError``
    and the caller (BestFitSelector) falls back to SES.
    """

    min_history = 10

    def predict(
        self,
        history: list[float],
        periods: int,
        *,
        deadline: float | None = None,
    ) -> list[dict[str, float]]:
        values = [float(value) for value in history]
        if len(values) < self.min_history:
            return _fallback(values, periods)

        try:
            from statsmodels.tsa.arima.model import ARIMA
        except ImportError:
            return _fallback(values, periods)

        try:
            fitted = self._fit_best(ARIMA, values, deadline=deadline)
            forecast = fitted.forecast(steps=periods)
        except Exception:
            return _fallback(values, periods)

        return [_bands(values, float(value)) for value in list(forecast)]

    def _fit_best(
        self,
        model_cls: Any,
        values: list[float],
        *,
        deadline: float | None = None,
    ):
        best_fit = None
        best_aic = float("inf")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for p in range(3):
                for d in range(2):
                    for q in range(3):
                        if deadline is not None and time.monotonic() >= deadline:
                            break
                        try:
                            fit = model_cls(values, order=(p, d, q)).fit()
                        except Exception:
                            continue
                        if fit.aic < best_aic:
                            best_fit = fit
                            best_aic = fit.aic
                    else:
                        continue
                    break
                else:
                    continue
                break
        if best_fit is None:
            raise ValueError("No ARIMA order converged (budget or data)")
        return best_fit


class SARIMAForecaster(ARIMAForecaster):
    """Seasonal ARIMA with the same non-seasonal AIC search."""

    def predict(
        self,
        history: list[float],
        periods: int,
        *,
        deadline: float | None = None,
    ) -> list[dict[str, float]]:
        values = [float(value) for value in history]
        if len(values) < self.min_history:
            return _fallback(values, periods)

        try:
            from statsmodels.tsa.statespace.sarimax import SARIMAX
        except ImportError:
            return _fallback(values, periods)

        season_length = 7 if len(values) >= 21 else max(2, min(6, len(values) // 2))
        try:
            fitted = self._fit_best_sarimax(SARIMAX, values, season_length, deadline=deadline)
            forecast = fitted.forecast(steps=periods)
        except Exception:
            return _fallback(values, periods)

        return [_bands(values, float(value)) for value in list(forecast)]

    def _fit_best_sarimax(
        self,
        model_cls: Any,
        values: list[float],
        season_length: int,
        *,
        deadline: float | None = None,
    ):
        best_fit = None
        best_aic = float("inf")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for p in range(3):
                for d in range(2):
                    for q in range(3):
                        if deadline is not None and time.monotonic() >= deadline:
                            break
                        try:
                            fit = model_cls(
                                values,
                                order=(p, d, q),
                                seasonal_order=(1, 0, 1, season_length),
                                enforce_stationarity=False,
                                enforce_invertibility=False,
                            ).fit(disp=False)
                        except Exception:
                            continue
                        if fit.aic < best_aic:
                            best_fit = fit
                            best_aic = fit.aic
                    else:
                        continue
                    break
                else:
                    continue
                break
        if best_fit is None:
            raise ValueError("No SARIMA order converged (budget or data)")
        return best_fit
