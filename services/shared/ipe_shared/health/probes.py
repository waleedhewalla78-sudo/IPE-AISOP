"""Deep health probes for IPE services."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.config import settings

logger = logging.getLogger(__name__)

_START_MONOTONIC = time.monotonic()


def uptime_seconds() -> int:
    return int(time.monotonic() - _START_MONOTONIC)


async def _timed_probe(coro_factory) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        await coro_factory()
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        return {"status": "up", "latency_ms": latency_ms}
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.debug("Health probe failed: %s", exc)
        return {"status": "down", "latency_ms": latency_ms}


async def probe_database(session: AsyncSession) -> dict[str, Any]:
    async def _check():
        await session.execute(text("SELECT 1"))

    return await _timed_probe(_check)


async def probe_redis() -> dict[str, Any]:
    async def _check():
        from ipe_shared.cache.redis_client import redis_client

        await redis_client.start()

    return await _timed_probe(_check)


def release_profile() -> str:
    return os.getenv("IPE_RELEASE_PROFILE", "").lower()


def kafka_required() -> bool:
    """Return True when Kafka connectivity must pass for a healthy service."""
    if release_profile() == "release1":
        return False
    kafka_enabled = os.getenv("IPE_KAFKA_ENABLED", "true").lower()
    if kafka_enabled in ("false", "0", "no"):
        return False
    return bool(settings.KAFKA_BOOTSTRAP_SERVERS)


def vault_required() -> bool:
    if release_profile() == "release1":
        return False
    return settings.VAULT_ENABLED


async def probe_kafka() -> dict[str, Any]:
    if not settings.KAFKA_BOOTSTRAP_SERVERS:
        return {"status": "not_configured"}

    async def _check():
        from aiokafka import AIOKafkaProducer

        producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
        await producer.start()
        await producer.stop()

    return await _timed_probe(_check)


async def probe_vault() -> dict[str, Any]:
    if not settings.VAULT_ENABLED:
        return {"status": "disabled"}

    async def _check():
        addr = settings.VAULT_ADDR.rstrip("/")
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(f"{addr}/v1/sys/health")
            if resp.status_code >= 500:
                raise RuntimeError(f"vault unhealthy: {resp.status_code}")

    return await _timed_probe(_check)


async def collect_dependencies(session: AsyncSession | None = None) -> dict[str, Any]:
    deps: dict[str, Any] = {}
    if session is not None:
        deps["database"] = await probe_database(session)
    else:
        deps["database"] = {"status": "unknown"}

    deps["redis"] = await probe_redis()
    if kafka_required():
        deps["kafka"] = await probe_kafka()
    else:
        reason = "release1_profile" if release_profile() == "release1" else "not_configured"
        deps["kafka"] = {"status": "skipped", "reason": reason}
    if vault_required():
        deps["vault"] = await probe_vault()
    else:
        reason = "release1_profile" if release_profile() == "release1" else "disabled"
        deps["vault"] = {"status": "skipped", "reason": reason}
    return deps


def overall_status(deps: dict[str, Any]) -> str:
    critical = ("database", "redis")
    ok_statuses = ("up", "disabled", "not_configured", "skipped")
    for key in critical:
        dep = deps.get(key, {})
        if dep.get("status") not in ok_statuses:
            return "degraded"
    optional_down = any(
        deps.get(k, {}).get("status") == "down"
        for k in ("kafka", "vault")
    )
    if optional_down:
        return "degraded"
    return "ok"


def allow_hs256_without_jwt_keys() -> bool:
    mode = os.getenv("IPE_JWT_SIGNING_MODE", settings.JWT_SIGNING_MODE).lower()
    return mode in ("hs256", "hs")
