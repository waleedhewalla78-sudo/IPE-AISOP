"""Shared MLflow utilities for model registry access."""

import os

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MLFLOW_S3_ENDPOINT_URL = os.getenv("MLFLOW_S3_ENDPOINT_URL", "")


def get_model_uri(model_name: str) -> str:
    """Return the MLflow model URI for the given registered model name.

    In production this points to the S3-backed model registry.
    In development it uses the local tracking server.
    """
    import mlflow

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    client = mlflow.tracking.MlflowClient()
    latest = client.get_latest_versions(model_name, stages=["Production"])
    if latest:
        return latest[0].source
    staging = client.get_latest_versions(model_name, stages=["Staging"])
    if staging:
        return staging[0].source
    return f"models:/{model_name}/latest"


def set_tracking_uri(uri: str | None = None) -> None:
    """Override the default MLflow tracking URI."""
    import mlflow

    mlflow.set_tracking_uri(uri or MLFLOW_TRACKING_URI)
