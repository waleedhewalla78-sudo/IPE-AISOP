from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "ipe-ml-svc"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = ""
    MLFLOW_TRACKING_URI: str = ""
    MODEL_CACHE_DIR: str = "/tmp/ml-models"
    DEFAULT_MODEL_VERSION: str = "production"
    FALLBACK_ENABLED: bool = True
    CORS_ORIGINS: list[str] = ["http://localhost:8082", "http://localhost:3000"]


settings = Settings()
