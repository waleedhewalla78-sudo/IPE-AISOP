"""Registry of required IPE secrets — rotation and provider mapping."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SecretSpec:
    name: str
    description: str
    required: bool
    default_for_dev: str
    provider_key: str
    rotates: bool = False


SECRETS_REGISTRY: list[SecretSpec] = [
    SecretSpec("JWT_SECRET_KEY", "Local JWT signing secret", True, "dev-secret-change-me", "jwt/secret", rotates=True),
    SecretSpec("DATABASE_URL", "PostgreSQL connection string", True, "postgresql://ipe:ipe_test_pass@localhost:5433/ipe_test", "db/url"),
    SecretSpec("REDIS_URL", "Redis connection string", True, "redis://localhost:6380/0", "redis/url"),
    SecretSpec("KAFKA_BOOTSTRAP_SERVERS", "Kafka broker list", True, "localhost:9092", "kafka/bootstrap"),
    SecretSpec("OPENROUTER_API_KEY", "OpenRouter LLM API key", False, "", "llm/openrouter"),
    SecretSpec("ANTHROPIC_API_KEY", "Anthropic API key", False, "", "llm/anthropic"),
    SecretSpec("STRIPE_SECRET_KEY", "Stripe billing secret", False, "sk_test_placeholder", "billing/stripe_secret"),
    SecretSpec("STRIPE_WEBHOOK_SECRET", "Stripe webhook signing secret", False, "whsec_placeholder", "billing/stripe_webhook"),
    SecretSpec("KEYCLOAK_CLIENT_SECRET", "Keycloak OIDC client secret", False, "", "auth/keycloak_client_secret"),
]
