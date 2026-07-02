"""Audit log export and MinIO archival helpers."""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.config import settings

logger = logging.getLogger(__name__)


async def fetch_audit_rows(
    session: AsyncSession,
    tenant_id: str,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 5000,
) -> list[dict[str, Any]]:
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, true)"),
        {"tid": tenant_id},
    )
    clauses = ["tenant_id = CAST(:tenant_id AS uuid)"]
    params: dict[str, Any] = {"tenant_id": tenant_id, "limit": limit}
    if start:
        clauses.append("timestamp >= :start")
        params["start"] = start
    if end:
        clauses.append("timestamp <= :end")
        params["end"] = end
    where = " AND ".join(clauses)
    result = await session.execute(
        text(
            f"""
            SELECT id, tenant_id, actor_type, actor_id, action, entity_type, entity_id,
                   before_state, after_state, rationale, timestamp
            FROM cdm_audit_log
            WHERE {where}
            ORDER BY timestamp DESC
            LIMIT :limit
            """
        ),
        params,
    )
    rows = []
    for row in result.mappings():
        rows.append(dict(row))
    return rows


def audit_rows_to_csv(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "id,tenant_id,actor_type,actor_id,action,entity_type,entity_id,timestamp\n"
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        serializable = {
            k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in row.items()
        }
        writer.writerow(serializable)
    return buf.getvalue()


async def archive_audit_csv_to_minio(csv_content: str, object_name: str) -> str | None:
    endpoint = settings.MINIO_ENDPOINT
    if not endpoint:
        return None
    try:
        from minio import Minio

        client = Minio(
            endpoint.replace("http://", "").replace("https://", ""),
            access_key=settings.MINIO_ACCESS_KEY or "ipe",
            secret_key=settings.MINIO_SECRET_KEY or "ipe-minio-pass",
            secure=endpoint.startswith("https"),
        )
        bucket = settings.MINIO_AUDIT_BUCKET
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
        data = csv_content.encode("utf-8")
        client.put_object(bucket, object_name, io.BytesIO(data), len(data), content_type="text/csv")
        return f"{bucket}/{object_name}"
    except Exception as exc:
        logger.warning("MinIO audit archive failed: %s", exc)
        return None
