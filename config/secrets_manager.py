"""
Secrets management — env vars (default) and Vault / AWS SM providers.

Activation: SECRETS_PROVIDER=env|hashi_vault|aws_sm
Vault: VAULT_ENABLED=true, VAULT_ADDR, VAULT_TOKEN
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SecretsProvider(ABC):
    @abstractmethod
    def get(self, key: str, default: str | None = None) -> str | None:
        ...


class EnvSecretsProvider(SecretsProvider):
    def get(self, key: str, default: str | None = None) -> str | None:
        return os.getenv(key, default)


class HashiVaultSecretsProvider(SecretsProvider):
    """Reads secrets via ipe_shared.config.vault_loader with env fallback."""

    def get(self, key: str, default: str | None = None) -> str | None:
        try:
            from ipe_shared.vault_loader import resolve_secret

            return resolve_secret(key, default=default)
        except ImportError:
            logger.warning("ipe_shared not available; falling back to env for %s", key)
            return os.getenv(key, default)


class AwsSecretsProvider(SecretsProvider):
    """AWS Secrets Manager — activation via boto3 (POST-B stub)."""

    def get(self, key: str, default: str | None = None) -> str | None:
        secret_id = os.getenv("AWS_SECRET_ID", key)
        region = os.getenv("AWS_REGION", "us-east-1")
        try:
            import boto3

            client = boto3.client("secretsmanager", region_name=region)
            resp = client.get_secret_value(SecretId=secret_id)
            return resp.get("SecretString", default)
        except Exception as exc:
            logger.debug("AWS SM read failed for %s: %s", secret_id, exc)
            return os.getenv(key, default)


def get_secrets_provider() -> SecretsProvider:
    provider = os.getenv("SECRETS_PROVIDER", "env").lower()
    if provider == "aws_sm":
        return AwsSecretsProvider()
    if provider in {"hashi_vault", "vault"}:
        return HashiVaultSecretsProvider()
    return EnvSecretsProvider()


def get_secret(key: str, default: str | None = None) -> str | None:
    return get_secrets_provider().get(key, default)
