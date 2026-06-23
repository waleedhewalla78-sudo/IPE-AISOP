from datetime import datetime
from typing import Any


def engineer_features(
    product_id: str,
    work_center_id: str,
    batch_size: float,
    operator_skill_tags: list[str] | None = None,
    hour_of_day: int | None = None,
    day_of_week: int | None = None,
    month: int | None = None,
) -> dict[str, Any]:
    now = datetime.now()
    features = {
        "product_id_hash": abs(hash(product_id)) % 1000,
        "work_center_id_hash": abs(hash(work_center_id)) % 100,
        "batch_size": float(batch_size),
        "batch_size_log": float(__import__("math").log(max(batch_size, 1))),
        "operator_skills_count": len(operator_skill_tags) if operator_skill_tags else 0,
        "hour_of_day": hour_of_day if hour_of_day is not None else now.hour,
        "day_of_week": day_of_week if day_of_week is not None else now.weekday(),
        "month": month if month is not None else now.month,
        "is_morning": 1 if (hour_of_day if hour_of_day is not None else now.hour) < 12 else 0,
        "is_weekend": 1 if (day_of_week if day_of_week is not None else now.weekday()) >= 5 else 0,
    }
    return features


def engineer_feature_vector(features: dict[str, Any]) -> list[float]:
    keys = [
        "product_id_hash",
        "work_center_id_hash",
        "batch_size",
        "batch_size_log",
        "operator_skills_count",
        "hour_of_day",
        "day_of_week",
        "month",
        "is_morning",
        "is_weekend",
    ]
    return [float(features.get(k, 0.0)) for k in keys]
