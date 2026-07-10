"""ARIMA-family forecasters with SES fallbacks."""

from __future__ import annotations

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
    """Auto-order ARIMA over a deliberately small search space."""

    min_history = 10

    def predict(self, history: list[float], periods: int) -> list[dict[str, float]]:
        values = [float(value) for value in history]
        if len(values) < self.min_history:
            return _fallback(values, periods)

        try:
            from statsmodels.tsa.arima.model import ARIMA
        except ImportError:
            return _fallback(values, periods)

        try:
            fitted = self._fit_best(ARIMA, values)
            forecast = fitted.forecast(steps=periods)
        except Exception:
            return _fallback(values, periods)

        return [_bands(values, float(value)) for value in list(forecast)]

    def _fit_best(self, model_cls: Any, values: list[float]):
        best_fit = None
        best_aic = float("inf")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for p in range(3):
                for d in range(2):
                    for q in range(3):
                        try:
                            fit = model_cls(values, order=(p, d, q)).fit()
                        except Exception:
                            continue
                        if fit.aic < best_aic:
                            best_fit = fit
                            best_aic = fit.aic
        if best_fit is None:
            raise ValueError("No ARIMA order converged")
        return best_fit


class SARIMAForecaster(ARIMAForecaster):
    """Seasonal ARIMA with the same non-seasonal AIC search."""

    def predict(self, history: list[float], periods: int) -> list[dict[str, float]]:
        values = [float(value) for value in history]
        if len(values) < self.min_history:
            return _fallback(values, periods)

        try:
            from statsmodels.tsa.statespace.sarimax import SARIMAX
        except ImportError:
            return _fallback(values, periods)

        season_length = 7 if len(values) >= 21 else max(2, min(6, len(values) // 2))
        try:
            fitted = self._fit_best_sarimax(SARIMAX, values, season_length)
            forecast = fitted.forecast(steps=periods)
        except Exception:
            return _fallback(values, periods)

        return [_bands(values, float(value)) for value in list(forecast)]

    def _fit_best_sarimax(self, model_cls: Any, values: list[float], season_length: int):
        best_fit = None
        best_aic = float("inf")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for p in range(3):
                for d in range(2):
                    for q in range(3):
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
        if best_fit is None:
            raise ValueError("No SARIMA order converged")
        return best_fit
