"""
Secrets management scaffold — supports env vars (current) and vault providers (POST-B).

Providers:
- env: current behavior, reads from environment variables
- aws_sm: AWS Secrets Manager
- hashi_vault: HashiCorp Vault

Activation: SECRETS_PROVIDER=env|aws_sm|hashi_vault
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod


class SecretsProvider(ABC):
    @abstractmethod
    def get(self, key: str, default: str | None = None) -> str | None:
        ...


class EnvSecretsProvider(SecretsProvider):
    def get(self, key: str, default: str | None = None) -> str | None:
        return os.getenv(key, default)


class AwsSecretsProvider(SecretsProvider):
    """POST-B: wire boto3 secretsmanager.get_secret_value."""

    def get(self, key: str, default: str | None = None) -> str | None:
        raise NotImplementedError("AWS Secrets Manager activation required (POST-B)")


class HashiVaultSecretsProvider(SecretsProvider):
    """POST-B: wire hvac client read."""

    def get(self, key: str, default: str | None = None) -> str | None:
        raise NotImplementedError("HashiCorp Vault activation required (POST-B)")


def get_secrets_provider() -> SecretsProvider:
    provider = os.getenv("SECRETS_PROVIDER", "env").lower()
    if provider == "aws_sm":
        return AwsSecretsProvider()
    if provider == "hashi_vault":
        return HashiVaultSecretsProvider()
    return EnvSecretsProvider()


def get_secret(key: str, default: str | None = None) -> str | None:
    return get_secrets_provider().get(key, default)
