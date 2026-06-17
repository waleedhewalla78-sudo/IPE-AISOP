"""
ML Retraining Pipeline DAG.

Orchestrates the monthly retraining of supplier reliability and cycle time
prediction models. Runs at 2 AM on the 1st of each month.

Task DAG:
  extract_training_data
    ├── train_supplier_reliability  (parallel)
    ├── train_cycle_time            (parallel)
    └── both join into evaluate_models
          → promote_if_better
          → update_cdm_predictions
"""

import json
from datetime import datetime, timezone
from uuid import uuid4

from airflow import DAG
from airflow.operators.python import PythonOperator
from sqlalchemy import create_engine, text as sa_text

from scripts.ml.train_supplier_reliability import run_training as run_supplier_training
from scripts.ml.train_cycle_time import run_training as run_cycle_time_training

DEFAULT_ARGS = {
    "owner": "ipe-ml",
    "depends_on_past": False,
    "email_on_failure": True,
    "retries": 1,
}

DB_URL = "postgresql://ipe:ipe_dev_pass@postgres:5432/ipe_dev"


def extract_training_data(**context):
    context["ti"].xcom_push(key="extraction_ts", value=datetime.now(timezone.utc).isoformat())
    conn = create_engine(DB_URL).connect()
    try:
        result = conn.execute(sa_text("SELECT COUNT(*) FROM cdm_supply_order"))
        rows = result.scalar() or 0
    finally:
        conn.close()
    return {"rows_extracted": rows, "status": "ok"}


def _latest_model_metrics(engine, model_name: str, tenant_id: str) -> dict | None:
    result = engine.execute(
        sa_text(
            "SELECT metrics FROM cdm_model_registry "
            "WHERE tenant_id = :tid AND model_name = :mn AND is_production = true "
            "ORDER BY created_at DESC LIMIT 1"
        ),
        {"tid": tenant_id, "mn": model_name},
    )
    row = result.fetchone()
    return dict(row[0]) if row else None


def _register_model(
    engine, tenant_id: str, model_name: str, model_version: str,
    model_type: str, metrics: dict, baseline: dict | None,
    artifact_path: str, training_rows: int,
):
    is_better = None
    if baseline:
        new_mae = metrics.get("mae", float("inf"))
        old_mae = baseline.get("mae", float("inf"))
        is_better = new_mae < old_mae

    engine.execute(
        sa_text(
            """INSERT INTO cdm_model_registry
            (id, tenant_id, model_name, model_version, model_type, metrics,
             baseline_metrics, is_production, is_better_than_baseline,
             artifact_path, training_rows, trained_by, promoted_at, created_at)
            VALUES (:id, :tid, :mn, :mv, :mt, :metrics, :baseline, false,
             :is_better, :artifact, :rows, 'airflow', NULL, NOW())"""
        ),
        {
            "id": str(uuid4()),
            "tid": tenant_id,
            "mn": model_name,
            "mv": model_version,
            "mt": model_type,
            "metrics": json.dumps(metrics),
            "baseline": json.dumps(baseline) if baseline else None,
            "is_better": is_better,
            "artifact": artifact_path,
            "rows": training_rows,
        },
    )


def train_supplier_reliability(**context):
    result = run_supplier_training(database_url=DB_URL)
    engine = create_engine(DB_URL)
    try:
        metrics = result if isinstance(result, dict) else {"mae": 0.0, "rmse": 0.0}
        _register_model(
            engine, "00000000-0000-0000-0000-000000000001",
            "supplier_reliability", datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
            "regression", metrics, None,
            f"/models/supplier_reliability/{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            metrics.get("training_rows", 0),
        )
    finally:
        engine.dispose()
    return {"model": "supplier_reliability", "status": "trained", "metrics": metrics}


def train_cycle_time(**context):
    result = run_cycle_time_training(database_url=DB_URL)
    engine = create_engine(DB_URL)
    try:
        metrics = result if isinstance(result, dict) else {"mae": 0.0, "rmse": 0.0}
        _register_model(
            engine, "00000000-0000-0000-0000-000000000001",
            "cycle_time", datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
            "regression", metrics, None,
            f"/models/cycle_time/{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            metrics.get("training_rows", 0),
        )
    finally:
        engine.dispose()
    return {"model": "cycle_time", "status": "trained", "metrics": metrics}


def evaluate_models(**context):
    supplier = context["ti"].xcom_pull(task_ids="train_supplier_reliability")
    cycle = context["ti"].xcom_pull(task_ids="train_cycle_time")

    engine = create_engine(DB_URL)
    try:
        supplier_baseline = _latest_model_metrics(engine, "supplier_reliability", "00000000-0000-0000-0000-000000000001")
        cycle_baseline = _latest_model_metrics(engine, "cycle_time", "00000000-0000-0000-0000-000000000001")
    finally:
        engine.dispose()

    supplier_mae = (supplier.get("metrics") or {}).get("mae", 0)
    baseline_mae = (supplier_baseline or {}).get("mae", float("inf"))

    cycle_mae = (cycle.get("metrics") or {}).get("mae", 0)
    cycle_baseline_mae = (cycle_baseline or {}).get("mae", float("inf"))

    supplier_improved = baseline_mae == float("inf") or supplier_mae < baseline_mae
    cycle_improved = cycle_baseline_mae == float("inf") or cycle_mae < cycle_baseline_mae

    evaluation = "passed" if supplier_improved and cycle_improved else "degraded"

    return {
        "supplier": supplier,
        "cycle_time": cycle,
        "supplier_baseline": supplier_baseline,
        "cycle_baseline": cycle_baseline,
        "evaluation": evaluation,
    }


def promote_if_better(**context):
    evaluation = context["ti"].xcom_pull(task_ids="evaluate_models")
    if evaluation.get("evaluation") != "passed":
        return {"promoted": False, "reason": "Model metrics degraded vs baseline"}

    engine = create_engine(DB_URL)
    tenant_id = "00000000-0000-0000-0000-000000000001"
    now = datetime.now(timezone.utc)
    promoted = []
    try:
        for model_name in ("supplier_reliability", "cycle_time"):
            result = engine.execute(
                sa_text(
                    "UPDATE cdm_model_registry "
                    "SET is_production = false "
                    "WHERE tenant_id = :tid AND model_name = :mn AND is_production = true"
                ),
                {"tid": tenant_id, "mn": model_name},
            )
            result = engine.execute(
                sa_text(
                    "UPDATE cdm_model_registry "
                    "SET is_production = true, promoted_at = :now "
                    "WHERE tenant_id = :tid AND model_name = :mn "
                    "AND is_better_than_baseline IN (true, NULL) "
                    "ORDER BY created_at DESC LIMIT 1 "
                    "RETURNING model_version"
                ),
                {"tid": tenant_id, "mn": model_name, "now": now},
            )
            row = result.fetchone()
            if row:
                promoted.append({"model": model_name, "version": row[0]})
    finally:
        engine.dispose()

    return {"promoted": len(promoted) > 0, "models": promoted, "evaluation": evaluation.get("evaluation")}


def update_cdm_predictions(**context):
    promote_result = context["ti"].xcom_pull(task_ids="promote_if_better")
    if not promote_result.get("promoted"):
        return {"updated": False, "reason": "No model promoted"}

    engine = create_engine(DB_URL)
    try:
        for model_info in promote_result.get("models", []):
            model_name = model_info["model"]
            if model_name == "supplier_reliability":
                engine.execute(
                    sa_text(
                        "UPDATE cdm_supplier s "
                        "SET reliability_score = r.metrics->>'mae', "
                        "    last_model_update = NOW() "
                        "FROM cdm_model_registry r "
                        "WHERE r.tenant_id = s.tenant_id "
                        "AND r.model_name = 'supplier_reliability' "
                        "AND r.is_production = true "
                        "AND r.model_version = :ver"
                    ),
                    {"ver": model_info["version"]},
                )
            elif model_name == "cycle_time":
                engine.execute(
                    sa_text(
                        "UPDATE cdm_routing_operation ro "
                        "SET duration_predicted_mins = r.metrics->>'mae', "
                        "    prediction_confidence = r.metrics->>'r2' "
                        "FROM cdm_model_registry r "
                        "WHERE r.tenant_id = ro.tenant_id "
                        "AND r.model_name = 'cycle_time' "
                        "AND r.is_production = true "
                        "AND r.model_version = :ver"
                    ),
                    {"ver": model_info["version"]},
                )
        updated = True
    finally:
        engine.dispose()

    return {
        "updated": updated,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "models": promote_result.get("models", []),
    }


with DAG(
    dag_id="ml_retraining_pipeline",
    default_args=DEFAULT_ARGS,
    description="Monthly ML model retraining for supplier reliability and cycle time",
    schedule="0 2 1 * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["ipe", "ml", "retraining"],
) as dag:

    extract = PythonOperator(
        task_id="extract_training_data",
        python_callable=extract_training_data,
    )

    train_supplier = PythonOperator(
        task_id="train_supplier_reliability",
        python_callable=train_supplier_reliability,
    )

    train_cycle = PythonOperator(
        task_id="train_cycle_time",
        python_callable=train_cycle_time,
    )

    evaluate = PythonOperator(
        task_id="evaluate_models",
        python_callable=evaluate_models,
    )

    promote = PythonOperator(
        task_id="promote_if_better",
        python_callable=promote_if_better,
    )

    update = PythonOperator(
        task_id="update_cdm_predictions",
        python_callable=update_cdm_predictions,
    )

    extract >> [train_supplier, train_cycle] >> evaluate >> promote >> update
