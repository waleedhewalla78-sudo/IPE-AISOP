"""Best-fit forecast model selection."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.forecaster import forecast_series as ses_forecast_series, mape
from app.core.forecasters.arima_forecaster import ARIMAForecaster, SARIMAForecaster


@dataclass(frozen=True)
class BestFitResult:
    points: list[dict[str, float]]
    version: str
    selected_model: str
    validation_mape: float | None
    intermittent: bool
    candidates: list[str]


class BestFitSelector:
    """Select a model with a small holdout validation pass."""

    model_versions = {"ses": "ses-v1", "arima": "arima-v1", "sarima": "sarima-v1"}

    def select_and_forecast(
        self,
        history: list[float],
        horizon: int,
        segment: str | None = None,
    ) -> BestFitResult:
        values = [float(value) for value in history]
        candidates = self._candidate_models(segment, values)
        selected_model, validation_mape = self._select_model(values, candidates)
        forecaster = self._forecaster(selected_model)
        points = forecaster.predict(values, horizon)
        return BestFitResult(
            points=points,
            version=f"best-fit:{self.model_versions[selected_model]}",
            selected_model=selected_model,
            validation_mape=validation_mape,
            intermittent=self._is_intermittent(values),
            candidates=candidates,
        )

    def _candidate_models(self, segment: str | None, history: list[float]) -> list[str]:
        if self._is_intermittent(history):
            return ["ses"]

        normalized = (segment or "").upper()
        if normalized in {"AX", "BX"}:
            return ["arima", "sarima", "ses"]
        if normalized in {"AY", "BY"}:
            return ["ses", "arima"]
        if normalized in {"AZ", "BZ", "CX", "CY", "CZ"}:
            return ["ses"]
        return ["ses", "arima", "sarima"]

    def _select_model(self, history: list[float], candidates: list[str]) -> tuple[str, float | None]:
        if len(history) < 6:
            return candidates[0], None

        train = history[:-3]
        actuals = history[-3:]
        best_model = candidates[0]
        best_mape = float("inf")
        for model_id in candidates:
            try:
                predictions = self._forecaster(model_id).predict(train, 3)
            except Exception:
                continue
            score = mape(actuals, [point["value"] for point in predictions])
            if score is not None and score < best_mape:
                best_model = model_id
                best_mape = score

        return best_model, None if best_mape == float("inf") else best_mape

    def _forecaster(self, model_id: str):
        if model_id == "arima":
            return ARIMAForecaster()
        if model_id == "sarima":
            return SARIMAForecaster()
        return _SesForecaster()

    def _is_intermittent(self, history: list[float]) -> bool:
        return bool(history) and (sum(1 for value in history if value == 0) / len(history)) > 0.30


class _SesForecaster:
    def predict(self, history: list[float], periods: int) -> list[dict[str, float]]:
        return ses_forecast_series(history, periods)
