from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from ipe_shared.config import settings


@dataclass
class JWKSConfig:
    jwks_url: str = ""
    cache_ttl: int = 3600
    algorithms: list[str] = field(default_factory=lambda: ["RS256"])

    @classmethod
    def from_settings(cls) -> JWKSConfig:
        return cls(
            jwks_url=getattr(settings, "JWT_JWKS_URL", "") or _build_keycloak_url(),
            cache_ttl=3600,
            algorithms=["RS256"],
        )


def _build_keycloak_url() -> str:
    keycloak_url = getattr(settings, "KEYCLOAK_URL", "")
    if not keycloak_url:
        return ""
    realm = getattr(settings, "KEYCLOAK_REALM", "ipe")
    return f"{keycloak_url}/realms/{realm}/protocol/openid-connect/certs"


class JWKSCache:
    def __init__(self, config: JWKSConfig | None = None) -> None:
        self._config = config or JWKSConfig.from_settings()
        self._keys: dict[str, Any] = {}
        self._raw_jwks: dict[str, Any] = {}
        self._expires_at: datetime = datetime.min.replace(tzinfo=None)
        self._lock = threading.Lock()

    def _is_expired(self) -> bool:
        return datetime.now(UTC) > self._expires_at

    def _refresh(self) -> None:
        import httpx

        url = self._config.jwks_url
        if not url:
            raise ValueError("JWKS URL is not configured")
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        jwks_data = response.json()
        self._raw_jwks = jwks_data
        new_keys: dict[str, Any] = {}
        for key_data in jwks_data.get("keys", []):
            kid = key_data.get("kid")
            if kid:
                new_keys[kid] = key_data
        self._keys = new_keys
        self._expires_at = datetime.now(UTC) + timedelta(seconds=self._config.cache_ttl)

    def get_signing_key(self, kid: str) -> Any:
        with self._lock:
            if self._is_expired() or kid not in self._keys:
                self._refresh()
            key_data = self._keys.get(kid)
            if key_data is None:
                raise jwt.InvalidTokenError(f"No matching key found for kid: {kid}")
            return jwt.algorithms.RSAAlgorithm.from_jwk(key_data)

    @property
    def raw_jwks(self) -> dict[str, Any]:
        with self._lock:
            if self._is_expired():
                self._refresh()
            return self._raw_jwks


_cache: JWKSCache | None = None


def _get_cache() -> JWKSCache:
    global _cache
    if _cache is None:
        _cache = JWKSCache()
    return _cache


class JWKSAuthBackend:
    def __init__(self, config: JWKSConfig | None = None) -> None:
        self._config = config or JWKSConfig.from_settings()
        self._cache = JWKSCache(self._config)

    def validate_token(self, token: str) -> dict[str, Any]:
        return self.decode_jwt(token)

    def decode_jwt(self, token: str) -> dict[str, Any]:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise jwt.InvalidTokenError("No kid in token header")

        signing_key = self._cache.get_signing_key(kid)

        issuer: str | None = None
        audience: str | None = None
        keycloak_url = getattr(settings, "KEYCLOAK_URL", "")
        if keycloak_url:
            realm = getattr(settings, "KEYCLOAK_REALM", "ipe")
            issuer = f"{keycloak_url}/realms/{realm}"
            audience = "ipe-platform"

        decode_opts: dict[str, Any] = {"verify_exp": True}
        decode_kwargs: dict[str, Any] = {
            "algorithms": self._config.algorithms,
            "options": decode_opts,
        }
        if issuer:
            decode_kwargs["issuer"] = issuer
        if audience:
            decode_kwargs["audience"] = audience

        return jwt.decode(token, signing_key, **decode_kwargs)


def get_jwks_public_keys() -> dict[str, Any]:
    cache = _get_cache()
    return cache.raw_jwks