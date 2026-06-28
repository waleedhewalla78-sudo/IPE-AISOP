from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "supply-svc"
    VERSION: str = "0.1.0"
    DATABASE_URL: str = "postgresql+asyncpg://ipe:ipe_dev_pass@localhost:5432/ipe_dev"
    CORS_ORIGINS: list[str] = ["http://localhost:8082"]
    MAT_SVC_URL: str = "http://mat-svc:8002"

    model_config = {"env_prefix": "IPE_", "case_sensitive": False}


settings = Settings()
