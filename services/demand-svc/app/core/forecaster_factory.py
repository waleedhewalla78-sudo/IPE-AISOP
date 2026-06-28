"""Forecasting strategy factory — SES, Prophet, LSTM with graceful fallbacks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from statistics import pstdev

from app.core.forecaster import forecast_series as ses_forecast_series, simple_exponential_smoothing


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


def select_forecaster(history: list[float]) -> tuple[BaseForecaster, str]:
    n = len(history)
    if n > 365:
        return LstmForecaster(), "lstm-v1"
    if n >= 30:
        return ProphetForecaster(), "prophet-v1"
    return SesForecaster(), "ses-v1"


def forecast_with_factory(history: list[float], periods: int) -> tuple[list[dict[str, float]], str]:
    forecaster, version = select_forecaster(history)
    try:
        return forecaster.predict(history, periods), version
    except Exception:
        return SesForecaster().predict(history, periods), "ses-v1"
