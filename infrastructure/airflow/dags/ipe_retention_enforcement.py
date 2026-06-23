"""Airflow DAG for IPE data retention enforcement (P9-009).

Runs daily at 03:00 UTC. Calls the compliance retention endpoint for each
entity type that has a configured retention policy.
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.http.operators.http import SimpleHttpOperator

ENTITY_TYPES = [
    "cdm_audit_log",
    "cdm_delay_event",
    "cdm_mdr_score",
    "cdm_demand_line",
    "cdm_manufacturing_order",
    "gdpr_dsar_request",
    "gdpr_consent",
]

default_args = {
    "owner": "ipe-platform",
    "depends_on_past": False,
    "email_on_failure": True,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="ipe_retention_enforcement",
    default_args=default_args,
    description="Daily data retention enforcement for IPE compliance (P9-009)",
    schedule_interval="0 3 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["ipe", "compliance", "retention", "daily"],
    max_active_runs=1,
    dagrun_timeout=timedelta(minutes=30),
) as dag:

    for entity_type in ENTITY_TYPES:
        _task = SimpleHttpOperator(
            task_id=f"enforce_retention_{entity_type}",
            http_conn_id="ipe_dpe_svc",
            endpoint="/api/v1/compliance/retention/enforce",
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-Tenant-ID": "{{ var.value.DEFAULT_TENANT_ID }}",
            },
            data=f'{{"entity_type": "{entity_type}"}}',
            response_check=lambda r: r.json().get("success", False),
        )