"""Edge Gateway Store-and-Forward Sync Engine.

This module implements the bi-directional sync engine for Edge Gateways,
handling outbound (push to cloud) and inbound (pull from cloud) synchronization.
"""
import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any

import httpx

from ipe_shared.edge.local_db import EdgeLocalDB

logger = logging.getLogger(__name__)


class SyncEngine:
    """Store-and-forward sync engine for Edge Gateway."""

    def __init__(
        self,
        local_db: EdgeLocalDB,
        cloud_url: str,
        gateway_id: str,
        api_key: str,
        sync_interval: int = 60,
        max_batch_size: int = 100,
        max_retries: int = 3,
        retry_delay: float = 5.0,
    ):
        self.local_db = local_db
        self.cloud_url = cloud_url.rstrip("/")
        self.gateway_id = gateway_id
        self.api_key = api_key
        self.sync_interval = sync_interval
        self.max_batch_size = max_batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._sync_loop())
        logger.info(f"Sync engine started for gateway {self.gateway_id}")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"Sync engine stopped for gateway {self.gateway_id}")

    async def _sync_loop(self) -> None:
        while self._running:
            try:
                await self._sync_cycle()
            except Exception as e:
                logger.error(f"Sync cycle failed: {e}")
            await asyncio.sleep(self.sync_interval)

    async def _sync_cycle(self) -> None:
        await self._push_outbound()
        await self._pull_inbound()

    async def _push_outbound(self) -> dict[str, Any]:
        pending = self.local_db.get_pending_sync_records(limit=self.max_batch_size)
        if not pending:
            return {"pushed": 0, "status": "no_pending"}

        batch_id = f"{self.gateway_id}_{int(time.time() * 1000)}"
        records = []
        for record in pending:
            records.append({
                "entity_type": record["entity_type"],
                "entity_id": record["entity_id"],
                "operation": record["operation"],
                "payload": record["payload"],
                "local_timestamp": record["local_timestamp"],
                "version": record["payload"].get("version", 1),
            })

        payload = {
            "batch_id": batch_id,
            "gateway_id": self.gateway_id,
            "batch_type": "operations",
            "records": records,
            "local_timestamp": datetime.now(UTC).isoformat(),
            "metadata": {
                "unsynced_counts": self.local_db.get_unsynced_count(),
            },
        }

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.cloud_url}/api/v1/edge/sync",
                        json=payload,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "X-Gateway-ID": self.gateway_id,
                            "Content-Type": "application/json",
                        },
                    )

                    if response.status_code == 200:
                        result = response.json()
                        record_ids = [r["id"] for r in pending]
                        self.local_db.mark_synced(record_ids)

                        for record in pending:
                            self.local_db.mark_entity_synced(
                                record["entity_type"],
                                record["entity_id"],
                                result.get("data", {}).get("version", 1),
                            )

                        logger.info(f"Pushed {len(pending)} records, batch {batch_id}")
                        return {"pushed": len(pending), "batch_id": batch_id, "status": "success"}

                    elif response.status_code == 409:
                        result = response.json()
                        conflicts = result.get("data", {}).get("conflicts", [])
                        for conflict in conflicts:
                            self._handle_push_conflict(conflict, pending)
                        return {"pushed": 0, "conflicts": len(conflicts), "status": "conflicts"}

                    else:
                        logger.warning(f"Push failed with status {response.status_code}")

            except httpx.ConnectError:
                logger.warning(f"Cloud unreachable, attempt {attempt + 1}/{self.max_retries}")
            except Exception as e:
                logger.error(f"Push error: {e}")

            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        for record in pending:
            self.local_db.mark_failed(record["id"], "max_retries_exceeded")
        return {"pushed": 0, "status": "failed"}

    def _handle_push_conflict(self, conflict: dict[str, Any], pending: list[dict]) -> None:
        entity_type = conflict.get("entity_type")
        entity_id = conflict.get("entity_id")
        conflict_type = conflict.get("conflict_type", "version_mismatch")

        if conflict_type == "version_mismatch":
            for record in pending:
                if record["entity_id"] == entity_id and record["entity_type"] == entity_type:
                    payload = record["payload"]
                    payload["conflict_status"] = "requires_manual_resolution"
                    payload["conflict_details"] = conflict
                    self.local_db._enqueue_sync(
                        entity_type, entity_id, "update", payload, record["local_timestamp"]
                    )
                    break

    async def _pull_inbound(self) -> dict[str, Any]:
        try:
            last_token = self.local_db.get_sync_meta("last_pull_token")

            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "gateway_id": self.gateway_id,
                    "hours_ahead": 24,
                }
                if last_token:
                    params["last_sync_token"] = last_token

                response = await client.get(
                    f"{self.cloud_url}/api/v1/edge/schedule/pull",
                    params=params,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "X-Gateway-ID": self.gateway_id,
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    deltas = result.get("data", {}).get("deltas", [])
                    sync_token = result.get("data", {}).get("sync_token", "")

                    for delta in deltas:
                        self.local_db.save_schedule(
                            delta.get("entity_type", ""),
                            delta.get("entity_id", ""),
                            delta.get("payload", {}),
                            delta.get("version", 1),
                        )

                    if sync_token:
                        self.local_db.set_sync_meta("last_pull_token", sync_token)

                    logger.info(f"Pulled {len(deltas)} schedule deltas")
                    return {"pulled": len(deltas), "status": "success"}

        except httpx.ConnectError:
            logger.warning("Cloud unreachable for pull")
        except Exception as e:
            logger.error(f"Pull error: {e}")

        return {"pulled": 0, "status": "failed"}

    async def push_batch(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        batch_id = f"{self.gateway_id}_{int(time.time() * 1000)}"
        payload = {
            "batch_id": batch_id,
            "gateway_id": self.gateway_id,
            "batch_type": "operations",
            "records": records,
            "local_timestamp": datetime.now(UTC).isoformat(),
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.cloud_url}/api/v1/edge/sync",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "X-Gateway-ID": self.gateway_id,
                        "Content-Type": "application/json",
                    },
                )
                return response.json()
        except Exception as e:
            logger.error(f"Batch push failed: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict[str, Any]:
        unsynced = self.local_db.get_unsynced_count()
        return {
            "gateway_id": self.gateway_id,
            "cloud_url": self.cloud_url,
            "sync_interval": self.sync_interval,
            "unsynced_records": unsynced,
            "total_unsynced": sum(unsynced.values()),
            "is_running": self._running,
        }
