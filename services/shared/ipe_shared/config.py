from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ipe:ipe_dev_pass@localhost:5432/ipe_dev"
    DATABASE_URL_SYNC: str = "postgresql://ipe:ipe_dev_pass@localhost:5432/ipe_dev"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET_KEY: str = "dev-only-change-in-production-min-32-chars-long!!"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 1440
    ANTHROPIC_API_KEY: str = "sk-ant-placeholder"
    SENTRY_DSN: str = ""
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "DEBUG"
    CORS_ORIGINS: str = "http://localhost:3000"
    SERVICE_NAME: str = "unknown"
    VERSION: str = "0.1.0"

    model_config = {"env_prefix": "IPE_", "case_sensitive": False}


settings = Settings()
