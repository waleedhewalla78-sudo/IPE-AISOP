"""Cycle time prediction model with MLflow tracking."""


def train_cycle_time_model(
    historical_cycle_times: list[float],
    tracking_uri: str = "http://localhost:5000",
) -> dict:
    import mlflow

    with mlflow.start_run(run_name="cycle_time_model") as run:
        n = len(historical_cycle_times)
        mu = sum(historical_cycle_times) / n if n > 0 else 0.0
        variance = sum((d - mu) ** 2 for d in historical_cycle_times) / n if n > 1 else 0.0
        sigma = variance ** 0.5

        mlflow.log_param("sample_size", n)
        mlflow.log_metric("mean_cycle_time", round(mu, 4))
        mlflow.log_metric("std_dev", round(sigma, 4))
        mlflow.log_metric("variance", round(variance, 4))
        mlflow.set_tag("model_type", "cycle_time_regression")

        return {
            "run_id": run.info.run_id,
            "mean_cycle_time": round(mu, 4),
            "std_dev": round(sigma, 4),
            "sample_size": n,
        }
