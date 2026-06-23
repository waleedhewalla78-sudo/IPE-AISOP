from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "scn-svc"
    VERSION: str = "0.1.0"
    LOG_LEVEL: str = "DEBUG"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

    model_config = {"env_prefix": "IPE_", "case_sensitive": False}


settings = Settings()