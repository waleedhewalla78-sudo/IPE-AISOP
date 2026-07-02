"""RSA key loading for RS256 JWT signing and verification."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from ipe_shared.config import settings

DEFAULT_KEY_ID = "ipe-rs256-v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _resolve_key_path(settings_value: str, env_name: str, default_relative: str) -> Path:
    if settings_value:
        return Path(settings_value)
    explicit = os.getenv(env_name)
    if explicit:
        return Path(explicit)
    return _repo_root() / default_relative


def get_private_key_path() -> Path:
    return _resolve_key_path(
        getattr(settings, "JWT_PRIVATE_KEY_PATH", ""),
        "IPE_JWT_PRIVATE_KEY_PATH",
        "config/keys/jwt-private.pem",
    )


def get_public_key_path() -> Path:
    return _resolve_key_path(
        getattr(settings, "JWT_PUBLIC_KEY_PATH", ""),
        "IPE_JWT_PUBLIC_KEY_PATH",
        "config/keys/jwt-public.pem",
    )


def get_trusted_keys_dir() -> Path:
    explicit = os.getenv("TRUSTED_KEYS_DIR") or os.getenv("IPE_TRUSTED_KEYS_DIR")
    if explicit:
        return Path(explicit)
    return _repo_root() / "config/keys/trusted"


def signing_mode() -> str:
    return str(getattr(settings, "JWT_SIGNING_MODE", "rs256")).lower()


def use_rs256_signing() -> bool:
    if signing_mode() == "hs256":
        return False
    if signing_mode() == "rs256":
        return get_private_key_path().exists()
    return settings.JWT_ALGORITHM.upper() == "RS256" and get_private_key_path().exists()


@lru_cache(maxsize=1)
def get_private_key_pem() -> str:
    path = get_private_key_path()
    key = path.read_text(encoding="utf-8")
    if "PRIVATE KEY" not in key:
        raise RuntimeError(f"Invalid private key at {path}")
    return key


@lru_cache(maxsize=1)
def get_public_key_pem() -> str:
    path = get_public_key_path()
    key = path.read_text(encoding="utf-8")
    if "PUBLIC KEY" not in key:
        raise RuntimeError(f"Invalid public key at {path}")
    return key


def get_key_id() -> str:
    return getattr(settings, "JWT_KEY_ID", DEFAULT_KEY_ID)


def get_all_public_keys() -> dict[str, str]:
    keys: dict[str, str] = {}
    current_kid = get_key_id()
    if get_public_key_path().exists():
        keys[current_kid] = get_public_key_pem()

    trusted_dir = get_trusted_keys_dir()
    if trusted_dir.exists():
        for path in sorted(trusted_dir.glob("jwt-public.pem.*")):
            kid = path.name.replace("jwt-public.pem.", "")
            keys[kid] = path.read_text(encoding="utf-8")
    return keys


def get_public_key_for_kid(kid: str | None) -> str:
    keys = get_all_public_keys()
    resolved = kid or get_key_id()
    if resolved not in keys:
        raise ValueError(f"Unknown key ID: {resolved}")
    return keys[resolved]
