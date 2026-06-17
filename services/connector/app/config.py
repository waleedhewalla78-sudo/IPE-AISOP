from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "ipe-odoo-connector"
    VERSION: str = "0.1.0"
    DATABASE_URL: str = "postgresql+asyncpg://ipe:ipe_dev_pass@localhost:5432/ipe_dev"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    LOG_LEVEL: str = "DEBUG"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    SYNC_INTERVAL_MINUTES: int = 15

    model_config = {"env_prefix": "IPE_", "case_sensitive": False}


settings = Settings()
