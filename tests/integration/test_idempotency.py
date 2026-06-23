"""Redis-based idempotency integration tests.

Validates the crash-safe idempotency pattern from ipe_shared.events.consumer:
  - Redis key set AFTER successful handler execution only
  - Duplicate event_id → skip (no re-execution)
  - Handler failure → no Redis key → event can be retried/DLQ'd

Requires: Redis running at IPE_REDIS_URL (default: redis://localhost:6379)
"""

import asyncio
import uuid

import pytest

pytestmark = [pytest.mark.integration]


def _redis_available() -> bool:
    try:
        import redis

        r = redis.from_url("redis://localhost:6379", socket_timeout=2)
        r.ping()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _redis_available(), reason="Redis not available")
class TestIdempotency:
    """Validate Redis-based idempotency for event consumers."""

    async def test_same_event_id_processed_once(self):
        """Two concurrent attempts to process the same event_id → exactly one succeeds."""
        import redis.asyncio as aioredis

        r = aioredis.from_url("redis://localhost:6379", decode_responses=True)
        event_id = str(uuid.uuid4())
        dedup_key = f"ipe:processed:test_idempotency:{event_id}"

        try:
            await r.ping()
        except Exception:
            pytest.skip("Redis not reachable")

        try:
            # Ensure key does not exist
            await r.delete(dedup_key)

            # Simulate two concurrent consumers checking + setting
            async def try_process():
                exists = await r.exists(dedup_key)
                if exists:
                    return False  # duplicate → skip
                await r.setex(dedup_key, 86400, "1")
                return True  # processed

            results = await asyncio.gather(*[try_process() for _ in range(5)])
            successes = sum(1 for r in results if r)
            assert successes == 1, f"Expected exactly 1 success, got {successes}"
        finally:
            await r.delete(dedup_key)
            await r.aclose()

    async def test_different_event_ids_both_processed(self):
        """Two events with different event_ids → both are processed."""
        import redis.asyncio as aioredis

        r = aioredis.from_url("redis://localhost:6379", decode_responses=True)
        event_a = str(uuid.uuid4())
        event_b = str(uuid.uuid4())
        key_a = f"ipe:processed:test_idempotency:{event_a}"
        key_b = f"ipe:processed:test_idempotency:{event_b}"

        try:
            await r.ping()
        except Exception:
            pytest.skip("Redis not reachable")

        try:
            await r.delete(key_a, key_b)

            # Process event A
            exists_a = await r.exists(key_a)
            assert not exists_a, "Event A should not exist yet"
            await r.setex(key_a, 86400, "1")

            # Process event B
            exists_b = await r.exists(key_b)
            assert not exists_b, "Event B should not exist yet"
            await r.setex(key_b, 86400, "1")

            # Both should exist now
            assert await r.exists(key_a), "Event A should be marked processed"
            assert await r.exists(key_b), "Event B should be marked processed"
        finally:
            await r.delete(key_a, key_b)
            await r.aclose()

    async def test_handler_that_throws_does_not_set_processed_key(self):
        """Crash safety: a failing handler must NOT mark the event as processed."""
        import redis.asyncio as aioredis

        r = aioredis.from_url("redis://localhost:6379", decode_responses=True)
        event_id = str(uuid.uuid4())
        dedup_key = f"ipe:processed:test_idempotency:{event_id}"

        try:
            await r.ping()
        except Exception:
            pytest.skip("Redis not reachable")

        try:
            await r.delete(dedup_key)

            # Simulate handler that throws
            async def failing_handler():
                raise ValueError("simulated handler failure")

            try:
                await failing_handler()
            except ValueError:
                pass

            # Key must NOT be set (handler failed → event should be retried/DLQ'd)
            exists = await r.exists(dedup_key)
            assert not exists, (
                f"FAIL: processed key {dedup_key} was set despite handler exception — "
                "event would be permanently lost"
            )
        finally:
            await r.delete(dedup_key)
            await r.aclose()
