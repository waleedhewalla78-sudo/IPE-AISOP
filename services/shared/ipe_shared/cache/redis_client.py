import logging

import redis.asyncio as aioredis

from ipe_shared.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self):
        self._client: aioredis.Redis | None = None

    async def start(self):
        self._client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
        await self._client.ping()
        logger.info("Redis connected: %s", settings.REDIS_URL)

    async def stop(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def check_and_set_dedup(self, key: str, ttl: int = 86400) -> bool:
        if self._client is None:
            return False
        exists = await self._client.exists(key)
        if exists:
            return True
        await self._client.setex(key, ttl, "1")
        return False

    async def check_key(self, key: str) -> bool:
        if self._client is None:
            return False
        return bool(await self._client.exists(key))

    async def set_key(self, key: str, value: str, ttl: int = 86400):
        if self._client:
            await self._client.setex(key, ttl, value)

    async def get_key(self, key: str) -> str | None:
        if self._client:
            return await self._client.get(key)
        return None


redis_client = RedisClient()
