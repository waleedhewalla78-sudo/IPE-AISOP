from ipe_shared.models.duration_prediction import DurationPrediction
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.work_order import WorkOrder

DRIFT_THRESHOLD_PCT = 10.0
MIN_RETRAIN_SAMPLES = 30
MIN_RETRAIN_SAMPLES_STRICT = 500


def analyze_mo_completion(
    mo: ManufacturingOrder,
    work_orders: list[WorkOrder],
) -> dict:
    planned_start = mo.planned_start
    planned_end = mo.planned_end
    actual_start = mo.actual_start
    actual_end = mo.actual_end

    if planned_start and planned_end:
        planned_duration = (planned_end - planned_start).total_seconds() / 86400.0
    elif work_orders:
        planned_duration = sum(
            (wo.duration_planned_mins or 0) for wo in work_orders
        ) / (24 * 60.0)
    else:
        planned_duration = 1.0

    if actual_start and actual_end:
        actual_duration = (actual_end - actual_start).total_seconds() / 86400.0
    elif work_orders:
        actual_duration = sum(
            (wo.duration_actual_mins or 0) for wo in work_orders
        ) / (24 * 60.0)
    else:
        actual_duration = planned_duration

    time_variance_pct = round(
        ((actual_duration - planned_duration) / planned_duration) * 100, 2
    ) if planned_duration else 0.0

    yield_planned = float(mo.yield_planned) if mo.yield_planned else 0.0
    yield_actual = float(mo.yield_actual) if mo.yield_actual else 0.0

    yield_variance_pct = round(
        ((yield_actual - yield_planned) / yield_planned) * 100, 2
    ) if yield_planned else 0.0

    scrap_delta = float(mo.scrap_actual) if mo.scrap_actual else 0.0

    completed_wo = sum(1 for wo in work_orders if wo.status == "completed")
    total_wo = len(work_orders)

    return {
        "mo_id": str(mo.id),
        "time_variance_pct": time_variance_pct,
        "yield_variance_pct": yield_variance_pct,
        "scrap_delta": scrap_delta,
        "planned_duration_days": round(planned_duration, 2),
        "actual_duration_days": round(actual_duration, 2),
        "completed_work_orders": completed_wo,
        "total_work_orders": total_wo,
    }


def calculate_prediction_drift(
    predictions: list[DurationPrediction],
) -> dict:
    """Calculate MAE drift between predicted and actual durations.

    Args:
        predictions: List of DurationPrediction records with predicted and actual values.

    Returns:
        Dict with mae, drift_detected, drift_pct, sample_count.
    """
    if not predictions:
        return {"mae": 0.0, "drift_detected": False, "drift_pct": 0.0, "sample_count": 0}

    errors = []
    for p in predictions:
        predicted = float(p.predicted_duration_mins or 0)
        actual = float(p.actual_duration_mins or 0)
        if actual > 0:
            errors.append(abs(predicted - actual))

    if not errors:
        return {"mae": 0.0, "drift_detected": False, "drift_pct": 0.0, "sample_count": 0}

    mae = sum(errors) / len(errors)

    baseline_mae = float(predictions[0].mae_30d) if predictions[0].mae_30d else None
    drift_pct = 0.0
    drift_detected = False

    if baseline_mae and baseline_mae > 0:
        drift_pct = round(((mae - baseline_mae) / baseline_mae) * 100, 2)
        drift_detected = abs(drift_pct) > DRIFT_THRESHOLD_PCT

    return {
        "mae": round(mae, 4),
        "drift_detected": drift_detected,
        "drift_pct": drift_pct,
        "sample_count": len(errors),
        "baseline_mae": baseline_mae,
    }


def should_trigger_retrain(drift_result: dict, strict: bool = False) -> bool:
    """Determine if model retraining should be triggered.

    Retrain if:
    - Drift is detected (>10% MAE change)
    - Sample count is sufficient (>=30 for normal, >=500 for strict/production)
    """
    min_samples = MIN_RETRAIN_SAMPLES_STRICT if strict else MIN_RETRAIN_SAMPLES
    return (
        drift_result.get("drift_detected", False)
        and drift_result.get("sample_count", 0) >= min_samples
    )


def evaluate_shadow_model(
    new_mae: float,
    current_mae: float,
    holdout_size: int,
) -> dict:
    """Shadow evaluation: only deploy new model if it beats current MAE.

    Args:
        new_mae: MAE of the newly trained model on hold-out set.
        current_mae: MAE of the current production model.
        holdout_size: Number of records in hold-out set.

    Returns:
        Dict with should_deploy, improvement_pct, rejection_reason.
    """
    if holdout_size < 10:
        return {
            "should_deploy": False,
            "improvement_pct": 0.0,
            "rejection_reason": "Hold-out set too small (<10 records)",
        }

    if current_mae <= 0:
        return {
            "should_deploy": True,
            "improvement_pct": 100.0,
            "rejection_reason": None,
        }

    improvement_pct = round(((current_mae - new_mae) / current_mae) * 100, 2)

    if new_mae >= current_mae:
        return {
            "should_deploy": False,
            "improvement_pct": improvement_pct,
            "rejection_reason": f"New MAE ({new_mae:.4f}) >= current MAE ({current_mae:.4f})",
        }

    if improvement_pct < 1.0:
        return {
            "should_deploy": False,
            "improvement_pct": improvement_pct,
            "rejection_reason": f"Improvement ({improvement_pct:.2f}%) below minimum threshold (1%)",
        }

    return {
        "should_deploy": True,
        "improvement_pct": improvement_pct,
        "rejection_reason": None,
    }


def build_retrain_payload(drift_result: dict, historical_records: list[dict]) -> dict:
    """Build payload for ml-svc retrain endpoint."""
    return {
        "historical_records": historical_records,
        "trigger_reason": "drift_detection",
        "drift_mae": drift_result.get("mae", 0),
        "drift_pct": drift_result.get("drift_pct", 0),
        "baseline_mae": drift_result.get("baseline_mae"),
    }
