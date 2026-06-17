from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "nlp-svc"
    VERSION: str = "0.1.0"
    DATABASE_URL: str = "postgresql+asyncpg://ipe:ipe_dev_pass@localhost:5432/ipe_dev"
    LOG_LEVEL: str = "DEBUG"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    ANTHROPIC_API_KEY: str = "sk-ant-placeholder"
    MODEL_CONFIG: dict = {"model": "claude-sonnet-4-20250514", "max_tokens": 1024}
    DPE_SVC_URL: str = "http://dpe-svc:8001"
    MAT_SVC_URL: str = "http://mat-svc:8002"
    CAP_SVC_URL: str = "http://cap-svc:8003"
    model_config = {"env_prefix": "IPE_", "case_sensitive": False}
settings = Settings()
