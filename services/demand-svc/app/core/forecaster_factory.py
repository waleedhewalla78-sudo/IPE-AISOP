"""Forecasting strategy factory — SES, ARIMA, Prophet, LSTM with graceful fallbacks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import overload
from statistics import pstdev

from app.core.forecaster import forecast_series as ses_forecast_series, simple_exponential_smoothing
from app.core.forecasters.arima_forecaster import ARIMAForecaster, SARIMAForecaster
from app.core.forecasters.model_selector import BestFitSelector


class BaseForecaster(ABC):
    @abstractmethod
    def predict(self, history: list[float], periods: int) -> list[dict[str, float]]:
        ...


class SesForecaster(BaseForecaster):
    def predict(self, history: list[float], periods: int) -> list[dict[str, float]]:
        return ses_forecast_series(history, periods)


class ProphetForecaster(BaseForecaster):
    def predict(self, history: list[float], periods: int) -> list[dict[str, float]]:
        if len(history) < 14:
            return SesForecaster().predict(history, periods)
        try:
            import pandas as pd
            from prophet import Prophet
        except ImportError:
            return SesForecaster().predict(history, periods)

        df = pd.DataFrame({"ds": pd.date_range("2024-01-01", periods=len(history), freq="D"), "y": history})
        model = Prophet(yearly_seasonality=False, weekly_seasonality=len(history) >= 14, daily_seasonality=False)
        model.fit(df)
        future = model.make_future_dataframe(periods=periods, freq="D")
        forecast = model.predict(future).tail(periods)
        spread = pstdev(history) if len(history) > 1 else max(history[-1] * 0.1, 1.0)
        return [
            {
                "value": round(float(row.yhat), 4),
                "lower": round(max(0.0, float(row.yhat) - 1.96 * spread), 4),
                "upper": round(float(row.yhat) + 1.96 * spread, 4),
            }
            for _, row in forecast.iterrows()
        ]


class LstmForecaster(BaseForecaster):
    def predict(self, history: list[float], periods: int) -> list[dict[str, float]]:
        if len(history) < 30:
            return ProphetForecaster().predict(history, periods)
        try:
            import torch
            import torch.nn as nn
        except ImportError:
            return ProphetForecaster().predict(history, periods)

        seq_len = min(14, len(history) - 1)
        values = history[-seq_len * 4 :] if len(history) > seq_len * 4 else history
        if len(values) < seq_len + 1:
            return ProphetForecaster().predict(history, periods)

        class _LSTM(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.lstm = nn.LSTM(1, 32, batch_first=True)
                self.fc = nn.Linear(32, 1)

            def forward(self, x):
                out, _ = self.lstm(x)
                return self.fc(out[:, -1, :])

        x, y = [], []
        for i in range(len(values) - seq_len):
            x.append(values[i : i + seq_len])
            y.append(values[i + seq_len])
        x_t = torch.tensor(x, dtype=torch.float32).unsqueeze(-1)
        y_t = torch.tensor(y, dtype=torch.float32).unsqueeze(-1)
        model = _LSTM()
        opt = torch.optim.Adam(model.parameters(), lr=0.01)
        loss_fn = nn.MSELoss()
        model.train()
        for _ in range(50):
            opt.zero_grad()
            pred = model(x_t)
            loss = loss_fn(pred, y_t)
            loss.backward()
            opt.step()

        model.eval()
        window = values[-seq_len:]
        points: list[dict[str, float]] = []
        spread = pstdev(history) if len(history) > 1 else max(history[-1] * 0.1, 1.0)
        with torch.no_grad():
            for _ in range(periods):
                inp = torch.tensor(window, dtype=torch.float32).view(1, seq_len, 1)
                val = float(model(inp).item())
                points.append(
                    {
                        "value": round(val, 4),
                        "lower": round(max(0.0, val - 1.96 * spread), 4),
                        "upper": round(val + 1.96 * spread, 4),
                    }
                )
                window = window[1:] + [val]
        return points


def select_forecaster(history: list[float], *, model: str = "ses") -> tuple[BaseForecaster, str]:
    """SES-first per Spec 017; Prophet/LSTM only when explicitly requested."""
    normalized = model.lower()
    if normalized == "arima" and len(history) >= 10:
        return ARIMAForecaster(), "arima-v1"  # type: ignore[return-value]
    if normalized == "sarima" and len(history) >= 10:
        return SARIMAForecaster(), "sarima-v1"  # type: ignore[return-value]
    if normalized == "lstm" and len(history) > 365:
        return LstmForecaster(), "lstm-v1"
    if normalized == "prophet" and len(history) >= 30:
        return ProphetForecaster(), "prophet-v1"
    return SesForecaster(), "ses-v1"


@overload
def forecast_with_factory(
    history: list[float],
    periods: int,
    *,
    model: str = "ses",
    segment: str | None = None,
    include_metadata: bool = False,
) -> tuple[list[dict[str, float]], str]: ...


@overload
def forecast_with_factory(
    history: list[float],
    periods: int,
    *,
    model: str = "ses",
    segment: str | None = None,
    include_metadata: bool = True,
) -> tuple[list[dict[str, float]], str, dict[str, object]]: ...


def forecast_with_factory(
    history: list[float],
    periods: int,
    *,
    model: str = "ses",
    segment: str | None = None,
    include_metadata: bool = False,
):
    normalized = model.lower()
    if normalized == "best_fit":
        try:
            result = BestFitSelector().select_and_forecast(history, periods, segment=segment)
            metadata: dict[str, object] = {
                "selected_model": result.selected_model,
                "validation_mape": result.validation_mape,
                "intermittent": result.intermittent,
                "candidates": result.candidates,
            }
            if include_metadata:
                return result.points, result.version, metadata
            return result.points, result.version
        except Exception:
            points = SesForecaster().predict(history, periods)
            metadata = {"selected_model": "ses", "validation_mape": None, "intermittent": False, "candidates": ["ses"]}
            if include_metadata:
                return points, "best-fit:ses-v1", metadata
            return points, "best-fit:ses-v1"

    forecaster, version = select_forecaster(history, model=normalized)
    try:
        points = forecaster.predict(history, periods)
        metadata = {"selected_model": version.removesuffix("-v1"), "validation_mape": None}
        if include_metadata:
            return points, version, metadata
        return points, version
    except Exception:
        points = SesForecaster().predict(history, periods)
        metadata = {"selected_model": "ses", "validation_mape": None}
        if include_metadata:
            return points, "ses-v1", metadata
        return points, "ses-v1"
