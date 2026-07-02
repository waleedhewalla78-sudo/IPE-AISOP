"""
HashiCorp Vault secret loader with environment-variable fallback.

Activation: VAULT_ENABLED=true + VAULT_ADDR + VAULT_TOKEN
Paths use KV v2 mount ``ipe`` (e.g. ``ipe/database`` → key ``password``).
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)

_VAULT_KEY_MAP: dict[str, tuple[str, str]] = {
    "DATABASE_PASSWORD": ("database", "password"),
    "IPE_DATABASE_PASSWORD": ("database", "password"),
    "JWT_SECRET_KEY": ("jwt", "secret"),
    "IPE_JWT_SECRET_KEY": ("jwt", "secret"),
    "ODOO_PASSWORD": ("odoo", "password"),
    "IPE_ODOO_PASSWORD": ("odoo", "password"),
    "KEYCLOAK_ADMIN_PASSWORD": ("keycloak", "admin_password"),
}


def vault_enabled() -> bool:
    flag = os.getenv("VAULT_ENABLED", "false").lower()
    return flag in {"1", "true", "yes", "on"}


def _vault_addr() -> str:
    return (os.getenv("VAULT_ADDR") or "http://localhost:8200").rstrip("/")


def _vault_token() -> str:
    return os.getenv("VAULT_TOKEN") or os.getenv("VAULT_DEV_ROOT_TOKEN_ID") or ""


@lru_cache(maxsize=1)
def _hvac_client() -> Any | None:
    if not vault_enabled():
        return None
    try:
        import hvac

        client = hvac.Client(url=_vault_addr(), token=_vault_token())
        if not client.is_authenticated():
            logger.warning("Vault client not authenticated at %s", _vault_addr())
            return None
        return client
    except Exception as exc:
        logger.warning("Vault client unavailable: %s", exc)
        return None


def get_vault_secret(path: str, key: str = "value", default: str | None = None) -> str | None:
    client = _hvac_client()
    if client is None:
        return default
    try:
        mount = os.getenv("VAULT_KV_MOUNT", "ipe")
        full_path = path.removeprefix(f"{mount}/").removeprefix("data/")
        resp = client.secrets.kv.v2.read_secret_version(path=full_path, mount_point=mount)
        data = resp.get("data", {}).get("data", {})
        value = data.get(key)
        if value is not None:
            return str(value)
    except Exception as exc:
        logger.debug("Vault read failed for %s/%s: %s", path, key, exc)
    return default


def resolve_secret(env_key: str, default: str | None = None) -> str | None:
    env_value = os.getenv(env_key)
    if env_value:
        return env_value
    if vault_enabled():
        mapping = _VAULT_KEY_MAP.get(env_key)
        if mapping:
            path, vault_key = mapping
            vault_value = get_vault_secret(path, vault_key)
            if vault_value:
                return vault_value
    return default


def clear_vault_cache() -> None:
    _hvac_client.cache_clear()
