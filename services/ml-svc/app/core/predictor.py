import logging
import tempfile
from typing import Any

import mlflow

from app.core.features import engineer_features, engineer_feature_vector
from app.config import settings

logger = logging.getLogger(__name__)

_model_cache: dict[str, Any] = {}


def _load_model(model_version: str = "production") -> Any | None:
    cache_key = f"model_{model_version}"
    if cache_key in _model_cache:
        return _model_cache[cache_key]

    if not settings.MLFLOW_TRACKING_URI:
        logger.warning("MLFLOW_TRACKING_URI not configured")
        return None

    try:
        client = mlflow.tracking.MlflowClient(settings.MLFLOW_TRACKING_URI)
        latest = client.get_latest_versions("duration_predictor", stages=[model_version])
        if not latest:
            logger.warning("No MLflow model found for version=%s", model_version)
            return None
        run_id = latest[0].run_id
        tmpdir = tempfile.mkdtemp()
        model_path = mlflow.artifacts.download_artifacts(
            run_id=run_id, artifact_path="model", dst_path=tmpdir
        )
        model = mlflow.sklearn.load_model(model_path)
        _model_cache[cache_key] = model
        return model
    except Exception as exc:
        logger.warning("Failed to load ML model from MLflow: %s", exc)
        return None


def _fallback_prediction(
    duration_planned_mins: float,
    historical_avg_ratio: float | None = None,
) -> dict:
    ratio = historical_avg_ratio if historical_avg_ratio is not None else 1.15
    predicted = duration_planned_mins * ratio
    return {
        "predicted_duration_mins": round(predicted, 2),
        "confidence": None,
        "model_version": "fallback",
        "fallback_used": True,
    }


def predict_duration(
    product_id: str,
    work_center_id: str,
    batch_size: float,
    duration_planned_mins: float,
    operator_skill_tags: list[str] | None = None,
    historical_avg_ratio: float | None = None,
    model_version: str = "production",
) -> dict:
    try:
        model = _load_model(model_version)
        if model is None:
            return _fallback_prediction(duration_planned_mins, historical_avg_ratio)

        features = engineer_features(
            product_id=product_id,
            work_center_id=work_center_id,
            batch_size=batch_size,
            operator_skill_tags=operator_skill_tags,
        )
        feature_vector = engineer_feature_vector(features)
        predicted_ratio = model.predict([feature_vector])[0]
        predicted_ratio = max(0.3, min(3.0, float(predicted_ratio)))
        predicted_mins = duration_planned_mins * predicted_ratio

        return {
            "predicted_duration_mins": round(predicted_mins, 2),
            "confidence": round(max(0, 1.0 - abs(predicted_ratio - 1.0) / 2.0), 4),
            "model_version": model_version,
            "fallback_used": False,
        }
    except Exception as exc:
        logger.warning("ML prediction failed: %s, falling back", exc)
        return _fallback_prediction(duration_planned_mins, historical_avg_ratio)
