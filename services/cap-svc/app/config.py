from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "cap-svc"
    VERSION: str = "0.1.0"
    DATABASE_URL: str = "postgresql+asyncpg://ipe:ipe_dev_pass@localhost:5432/ipe_dev"
    LOG_LEVEL: str = "DEBUG"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    ML_SVC_URL: str = "http://ml-svc:8011"
    DPE_SVC_URL: str = "http://dpe-svc:8001"
    MDR_QUALITY_GATE_THRESHOLD: float = 70.0
    MAX_BOM_DEPTH: int = 5
    model_config = {"env_prefix": "IPE_", "case_sensitive": False}
settings = Settings()
