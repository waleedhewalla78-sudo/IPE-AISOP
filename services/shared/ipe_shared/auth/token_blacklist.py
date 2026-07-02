"""JWT revocation blacklist backed by Redis."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import redis.asyncio as aioredis

from ipe_shared.config import settings

logger = logging.getLogger(__name__)

_blacklist_client: aioredis.Redis | None = None


def _blacklist_url() -> str:
    base = settings.REDIS_URL.rstrip("/")
  # Use DB 1 for token blacklist (dedup uses default DB 0)
    if base.endswith("/0"):
        return base[:-1] + "1"
    if "/" not in base.split("://", 1)[-1]:
        return f"{base}/1"
    return base


async def _get_client() -> aioredis.Redis | None:
    global _blacklist_client
    if _blacklist_client is None:
        try:
            _blacklist_client = aioredis.from_url(_blacklist_url(), decode_responses=True)
            await _blacklist_client.ping()
        except Exception as exc:
            logger.warning("JWT blacklist Redis unavailable: %s", exc)
            return None
    return _blacklist_client


async def blacklist_token(jti: str, exp: int) -> None:
    """Blacklist a token by JTI until its natural expiry."""
    if not jti:
        return
    client = await _get_client()
    if client is None:
        return
    ttl = int(exp) - int(datetime.now(UTC).timestamp())
    if ttl > 0:
        await client.setex(f"blacklist:{jti}", ttl, "1")


async def is_token_blacklisted(jti: str | None) -> bool:
    if not jti:
        return False
    client = await _get_client()
    if client is None:
        return False
    return bool(await client.exists(f"blacklist:{jti}"))
