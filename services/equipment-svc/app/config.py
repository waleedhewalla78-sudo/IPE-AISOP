from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "equipment-svc"
    VERSION: str = "0.1.0"
    DATABASE_URL: str = "postgresql+asyncpg://ipe:ipe_dev_pass@localhost:5432/ipe_dev"
    CORS_ORIGINS: list[str] = ["http://localhost:8082"]
    RUL_CRITICAL_HOURS: float = 48.0

    model_config = {"env_prefix": "IPE_", "case_sensitive": False}


settings = Settings()
