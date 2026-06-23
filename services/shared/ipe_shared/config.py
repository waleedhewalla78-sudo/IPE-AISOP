from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ipe:ipe_dev_pass@localhost:5432/ipe_dev"
    DATABASE_URL_SYNC: str = "postgresql://ipe:ipe_dev_pass@localhost:5432/ipe_dev"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    SCHEMA_REGISTRY_URL: str = "http://localhost:8083"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 1440
    JWT_USE_JWKS: bool = False
    JWT_JWKS_URL: str = ""
    KEYCLOAK_URL: str = ""
    KEYCLOAK_REALM: str = "ipe"
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

    model_config = {"env_prefix": "IPE_", "case_sensitive": False}

    def model_post_init(self, __context):
        if not self.JWT_SECRET_KEY and self.ENVIRONMENT == "production":
            raise ValueError(
                "JWT_SECRET_KEY must be set in production environment. "
                "Generate a random secret: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )


settings = Settings()
