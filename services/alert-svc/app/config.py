from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "alert-svc"
    VERSION: str = "0.1.0"
    LOG_LEVEL: str = "DEBUG"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "alerts@ipe.local"
    ALERT_RECIPIENT: str = "planner@ipe.local"

    model_config = {"env_prefix": "IPE_", "case_sensitive": False}


settings = Settings()
