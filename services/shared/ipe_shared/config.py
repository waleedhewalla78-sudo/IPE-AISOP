from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ipe:ipe_dev_pass@localhost:5432/ipe_dev"
    DATABASE_URL_SYNC: str = "postgresql://ipe:ipe_dev_pass@localhost:5432/ipe_dev"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    SCHEMA_REGISTRY_URL: str = "http://localhost:8083"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_SIGNING_MODE: str = "rs256"
    JWT_PRIVATE_KEY_PATH: str = ""
    JWT_PUBLIC_KEY_PATH: str = ""
    JWT_KEY_ID: str = "ipe-rs256-v1"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 1440
    JWT_USE_JWKS: bool = False
    JWT_JWKS_URL: str = ""
    KEYCLOAK_URL: str = ""
    KEYCLOAK_REALM: str = "ipe"
    KEYCLOAK_CLIENT_ID: str = "ipe-platform"
    KEYCLOAK_CLIENT_SECRET: str = ""
    KEYCLOAK_PUBLIC_URL: str = "http://localhost:8180"
    AUTH_MODE: str = "local"
    ANTHROPIC_API_KEY: str = ""
    SENTRY_DSN: str = ""
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "DEBUG"
    CORS_ORIGINS: str = "http://localhost:3000"
    SERVICE_NAME: str = "unknown"
    VERSION: str = "0.1.0"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    OTEL_EXPORTER_OTLP_METRICS_ENDPOINT: str = ""
    OTEL_TRACING_ENABLED: bool = True
    OTEL_LOGGING_ENABLED: bool = True
    PAGERDUTY_ROUTING_KEY: str = ""
    ALERTMANAGER_URL: str = ""
    VAULT_ENABLED: bool = False
    VAULT_ADDR: str = "http://localhost:8200"
    VAULT_TOKEN: str = ""
    VAULT_KV_MOUNT: str = "ipe"
    SECRETS_PROVIDER: str = "env"
    AUDIT_REQUEST_MIDDLEWARE: bool = False
    AUDIT_KAFKA_ENABLED: bool = False
    AUDIT_KAFKA_TOPIC: str = "ipe.audit.v3"
    MINIO_ENDPOINT: str = ""
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_AUDIT_BUCKET: str = "ipe-audit-archive"

    model_config = {"env_prefix": "IPE_", "case_sensitive": False}

    def model_post_init(self, __context):
        try:
            from ipe_shared.vault_loader import resolve_secret

            if not self.JWT_SECRET_KEY:
                self.JWT_SECRET_KEY = resolve_secret("IPE_JWT_SECRET_KEY") or resolve_secret(
                    "JWT_SECRET_KEY", ""
                ) or self.JWT_SECRET_KEY
        except ImportError:
            pass
        if not self.JWT_SECRET_KEY and self.ENVIRONMENT == "production":
            raise ValueError(
                "JWT_SECRET_KEY must be set in production environment. "
                "Generate a random secret: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )


settings = Settings()
