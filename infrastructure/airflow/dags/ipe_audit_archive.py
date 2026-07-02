"""Daily audit log archival to MinIO via compliance export API."""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.http.operators.http import SimpleHttpOperator

default_args = {
    "owner": "ipe-platform",
    "depends_on_past": False,
    "email_on_failure": True,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    dag_id="ipe_audit_archive",
    default_args=default_args,
    description="Daily audit CSV export and MinIO archive (Phase 0.5)",
    schedule_interval="0 2 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["ipe", "compliance", "audit", "daily"],
    max_active_runs=1,
) as dag:

    archive_audit = SimpleHttpOperator(
        task_id="archive_audit_csv",
        http_conn_id="ipe_dpe_svc",
        endpoint="/api/v1/compliance/audit/export?format=csv&archive=true",
        method="GET",
        headers={
            "X-Tenant-ID": "{{ var.value.DEFAULT_TENANT_ID }}",
            "Authorization": "Bearer {{ var.value.IPE_ADMIN_TOKEN }}",
        },
        response_check=lambda r: r.status_code == 200,
    )
