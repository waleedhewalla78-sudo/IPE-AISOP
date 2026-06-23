from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.http.operators.http import SimpleHttpOperator

default_args = {
    "owner": "ipe-platform",
    "depends_on_past": False,
    "email_on_failure": True,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="ipe_daily_sop_pipeline",
    default_args=default_args,
    description="Daily S&OP forecast ingestion and gap analysis",
    schedule_interval="0 6 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["ipe", "sop", "daily"],
) as dag:

    ingest_forecast = SimpleHttpOperator(
        task_id="ingest_sop_forecast",
        http_conn_id="ipe_dpe_svc",
        endpoint="/api/v1/sop/forecast",
        method="POST",
        headers={"Content-Type": "application/json", "X-Tenant-ID": "{{ var.value.DEFAULT_TENANT_ID }}"},
        data='{"source": "airflow_daily", "horizon_weeks": 52}',
        response_check=lambda r: r.json().get("success", False),
    )

    solve_sop = SimpleHttpOperator(
        task_id="solve_sop_gap",
        http_conn_id="ipe_dpe_svc",
        endpoint="/api/v1/sop/solve",
        method="POST",
        headers={"Content-Type": "application/json", "X-Tenant-ID": "{{ var.value.DEFAULT_TENANT_ID }}"},
        data='{"threshold_pct": 15.0}',
        response_check=lambda r: r.json().get("success", False),
    )

    ingest_forecast >> solve_sop

with DAG(
    dag_id="ipe_hourly_schedule_pipeline",
    default_args=default_args,
    description="Hourly finite-capacity scheduling with cost optimization",
    schedule_interval="0 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["ipe", "scheduling", "hourly"],
) as hourly_dag:

    run_schedule = SimpleHttpOperator(
        task_id="run_capacity_schedule",
        http_conn_id="ipe_cap_svc",
        endpoint="/api/v1/capacity/schedule",
        method="POST",
        headers={"Content-Type": "application/json", "X-Tenant-ID": "{{ var.value.DEFAULT_TENANT_ID }}"},
        data='{"horizon_days": 7}',
        response_check=lambda r: r.json().get("success", False),
    )

    run_cost_optimized = SimpleHttpOperator(
        task_id="run_cost_optimized_schedule",
        http_conn_id="ipe_cap_svc",
        endpoint="/api/v1/capacity/cost-optimized",
        method="POST",
        headers={"Content-Type": "application/json", "X-Tenant-ID": "{{ var.value.DEFAULT_TENANT_ID }}"},
        data='{"alpha": 0.7, "horizon_days": 7}',
        response_check=lambda r: r.json().get("success", False),
    )

    run_schedule >> run_cost_optimized

with DAG(
    dag_id="ipe_nightly_material_pipeline",
    default_args=default_args,
    description="Nightly material ATP and procurement pipeline",
    schedule_interval="0 2 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["ipe", "material", "nightly"],
) as nightly_dag:

    run_patp = SimpleHttpOperator(
        task_id="run_probabilistic_atp",
        http_conn_id="ipe_mat_svc",
        endpoint="/api/v1/material/probabilistic-atp",
        method="POST",
        headers={"Content-Type": "application/json", "X-Tenant-ID": "{{ var.value.DEFAULT_TENANT_ID }}"},
        data='{"simulations": 1000}',
        response_check=lambda r: r.json().get("success", False),
    )

    run_ctp = SimpleHttpOperator(
        task_id="run_ctp_batch",
        http_conn_id="ipe_mat_svc",
        endpoint="/api/v1/material/ctp/batch",
        method="POST",
        headers={"Content-Type": "application/json", "X-Tenant-ID": "{{ var.value.DEFAULT_TENANT_ID }}"},
        data='{}',
        response_check=lambda r: r.json().get("success", False),
    )

    run_patp >> run_ctp