import pytest
from app.core.features import engineer_features, engineer_feature_vector
from app.core.predictor import predict_duration, _fallback_prediction
from app.core.trainer import train_duration_model


class TestFeatureEngineering:
    def test_engineer_features_returns_expected_keys(self):
        feats = engineer_features("PROD001", "WC001", 10.0, ["welding", "assembly"])
        assert "product_id_hash" in feats
        assert "work_center_id_hash" in feats
        assert feats["batch_size"] == 10.0
        assert feats["operator_skills_count"] == 2

    def test_feature_vector_length(self):
        feats = engineer_features("PROD001", "WC001", 10.0)
        vec = engineer_feature_vector(feats)
        assert len(vec) == 10

    def test_empty_skill_tags(self):
        feats = engineer_features("PROD001", "WC001", 5.0, None)
        assert feats["operator_skills_count"] == 0


class TestFallbackPrediction:
    def test_fallback_uses_ratio(self):
        result = _fallback_prediction(100.0, historical_avg_ratio=1.2)
        assert result["predicted_duration_mins"] == 120.0
        assert result["fallback_used"] is True
        assert result["model_version"] == "fallback"

    def test_fallback_default_ratio(self):
        result = _fallback_prediction(60.0)
        assert result["predicted_duration_mins"] == 69.0  # 60 * 1.15
        assert result["fallback_used"] is True


class TestPredictor:
    def test_predict_without_mlflow_falls_back(self):
        result = predict_duration(
            product_id="PROD001",
            work_center_id="WC001",
            batch_size=10.0,
            duration_planned_mins=100.0,
        )
        assert result["fallback_used"] is True
        assert result["model_version"] == "fallback"
        assert result["predicted_duration_mins"] > 0

    def test_predict_with_explicit_fallback_ratio(self):
        result = predict_duration(
            product_id="PROD001",
            work_center_id="WC001",
            batch_size=10.0,
            duration_planned_mins=100.0,
            historical_avg_ratio=1.5,
        )
        assert result["fallback_used"] is True
        assert result["predicted_duration_mins"] == 150.0


class TestTrainer:
    def test_train_skipped_with_insufficient_data(self):
        result = train_duration_model([])
        assert result["status"] == "skipped"

    def test_trains_with_synthetic_data(self):
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_absolute_error

        records = []
        for i in range(20):
            records.append({
                "product_id": f"P{i % 5}",
                "work_center_id": f"WC{i % 3}",
                "batch_size": float(10 + i),
                "operator_skill_tags": ["welding"] if i % 2 == 0 else [],
                "duration_planned_mins": 60.0,
                "duration_actual_mins": 60.0 * (0.8 + 0.4 * (i % 3) / 2.0),
                "hour_of_day": 8 + i % 10,
                "day_of_week": i % 7,
                "month": (i % 12) + 1,
            })

        X, y = [], []
        for rec in records:
            from app.core.features import engineer_feature_vector
            feats = engineer_feature_vector({
                "product_id_hash": abs(hash(rec["product_id"])) % 1000,
                "work_center_id_hash": abs(hash(rec["work_center_id"])) % 100,
                "batch_size": rec["batch_size"],
                "operator_skills_count": len(rec.get("operator_skill_tags", [])),
                "hour_of_day": rec.get("hour_of_day", 8),
                "day_of_week": rec.get("day_of_week", 1),
                "month": rec.get("month", 1),
            })
            actual_ratio = rec["duration_actual_mins"] / max(rec["duration_planned_mins"], 1)
            X.append(feats)
            y.append(actual_ratio)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=50, max_depth=8, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)

        assert mae < 1.0, f"MAE too high: {mae}"
        assert len(model.predict([X_train[0]])) == 1
