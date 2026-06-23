import tempfile
from datetime import UTC, datetime

import mlflow
from mlflow.models import infer_signature

from app.core.features import engineer_feature_vector


def _build_training_data(historical_records: list[dict]) -> tuple[list[list[float]], list[float]]:
    X, y = [], []
    for rec in historical_records:
        feats = engineer_feature_vector({
            "product_id_hash": abs(hash(rec.get("product_id", ""))) % 1000,
            "work_center_id_hash": abs(hash(rec.get("work_center_id", ""))) % 100,
            "batch_size": float(rec.get("batch_size", 1)),
            "operator_skills_count": len(rec.get("operator_skill_tags", [])),
            "hour_of_day": rec.get("hour_of_day", 8),
            "day_of_week": rec.get("day_of_week", 1),
            "month": rec.get("month", 1),
        })
        actual_ratio = float(rec.get("duration_actual_mins", 0)) / max(float(rec.get("duration_planned_mins", 1)), 1)
        X.append(feats)
        y.append(actual_ratio)
    return X, y


def train_duration_model(
    historical_records: list[dict],
    model_name: str = "duration_predictor",
    experiment_name: str = "ipe-duration-prediction",
) -> dict:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score

    X, y = _build_training_data(historical_records)
    if len(X) < 10:
        return {"status": "skipped", "reason": "Insufficient training data (<10 records)"}

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    baseline_mae = sum(abs(y - 1.0) for y in y_test) / len(y_test) if y_test else 1.0

    with tempfile.TemporaryDirectory() as tmpdir:
        import pickle
        model_path = f"{tmpdir}/model.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(model, f)

        mlflow.set_experiment(experiment_name)
        with mlflow.start_run(run_name=f"{model_name}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"):
            mlflow.log_param("model_type", "RandomForestRegressor")
            mlflow.log_param("n_estimators", 100)
            mlflow.log_param("max_depth", 10)
            mlflow.log_param("training_records", len(X))
            mlflow.log_metric("mae", mae)
            mlflow.log_metric("r2", r2)
            mlflow.log_metric("baseline_mae", baseline_mae)
            mlflow.log_metric("is_better_than_baseline", 1 if mae < baseline_mae else 0)

            signature = infer_signature(X_train, y_pred)
            mlflow.sklearn.log_model(model, "model", signature=signature)
            mlflow.register_model(f"runs:/{mlflow.active_run().info.run_id}/model", model_name)

    return {
        "status": "trained",
        "model_name": model_name,
        "mae": mae,
        "r2": r2,
        "baseline_mae": baseline_mae,
        "is_better_than_baseline": mae < baseline_mae,
        "training_records": len(X),
    }
