from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "del-svc"
    VERSION: str = "0.1.0"
    DATABASE_URL: str = "postgresql+asyncpg://ipe:ipe_dev_pass@localhost:5432/ipe_dev"
    LOG_LEVEL: str = "DEBUG"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    model_config = {"env_prefix": "IPE_", "case_sensitive": False}
settings = Settings()
