# IPE Airflow Production Hardening
# Apply these changes to docker-compose.yml for production

# Environment variables to add to airflow services:
# AIRFLOW__CORE__AUTH_MANAGER: airflow.utils.authenticator.PasswordAuthenticator
# AIRFLOW__WEBSERVER__RBAC: "True"
# AIRFLOW__WEBSERVER__WEB_SERVER_CONFIG: /opt/airflow/webserver_config.py
# AIRFLOW__CORE__EXECUTOR: CeleryExecutor
# AIRFLOW__CELERY__BROKER_URL: redis://redis:6379/0
# AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@db:5432/airflow
# AIRFLOW__CORE__FERNET_KEY: <generated-fernet-key>
# AIRFLOW__WEBSERVER__SECRET_KEY: <generated-secret-key>

# webserver_config.py content for Airflow
webserver_config = """
from airflow.configuration import conf
from flask_appbuilder.security.manager import AUTH_DB

AUTH_TYPE = AUTH_DB
AUTH_ROLE_ADMIN = 'Admin'
AUTH_ROLE_PUBLIC = 'Public'
AUTH_USER_REGISTRATION = False
AUTH_USER_REGISTRATION_ROLE = 'Viewer'

# Restrict to IPE tenant users only
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*.ipe.ai']
"""

# Health check commands
HEALTHCHECK_DAGS = [
    "airflow dags list",
    "airflow dags test ipe_daily_sop_pipeline 2026-01-01",
    "airflow dags test ipe_retention_enforcement 2026-01-01",
]

# TLS configuration for production
TLS_CONFIG = """
AIRFLOW__WEBSERVER__WEB_SERVER_SSL_CERT: /opt/airflow/certs/tls.crt
AIRFLOW__WEBSERVER__WEB_SERVER_SSL_KEY: /opt/airflow/certs/tls.key
AIRFLOW__WEBSERVER__BASE_URL: https://airflow.ipe.ai
"""
