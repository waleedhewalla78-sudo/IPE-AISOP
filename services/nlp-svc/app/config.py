from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "nlp-svc"
    VERSION: str = "0.1.0"
    DATABASE_URL: str = "postgresql+asyncpg://ipe:ipe_dev_pass@localhost:5432/ipe_dev"
    LOG_LEVEL: str = "DEBUG"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    LLM_TIER_DEFAULT: int = 1
    LLM_ROUTING_ENABLED: bool = False
    LLM_PRIMARY_PROVIDER: str = "auto"  # auto | ollama | openrouter | anthropic
    ANTHROPIC_API_KEY: str = "sk-ant-placeholder"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "google/gemini-2.5-flash"
    SAGEMAKER_ENDPOINT_URL: str = ""
    OLLAMA_ENDPOINT_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    VLLM_ENDPOINT_URL: str = ""
    AWS_REGION: str = "us-east-1"
    MODEL_CONFIG: dict = {"model": "claude-sonnet-4-20250514", "max_tokens": 1024}
    DPE_SVC_URL: str = "http://dpe-svc:8001"
    MAT_SVC_URL: str = "http://mat-svc:8002"
    CAP_SVC_URL: str = "http://cap-svc:8003"
    FEA_SVC_URL: str = "http://fea-svc:8004"
    RES_SVC_URL: str = "http://res-svc:8005"
    CONNECTOR_SVC_URL: str = "http://connector:8009"
    ALERT_SVC_URL: str = "http://alert-svc:8010"
    DEMAND_SVC_URL: str = "http://demand-svc:8040"
    SOP_SVC_URL: str = "http://sop-svc:8110"
    COPILOT_SHADOW_MODE: bool = True
    COPILOT_TIMEOUT_SECONDS: int = 300
    model_config = {"env_prefix": "IPE_", "case_sensitive": False}
settings = Settings()
