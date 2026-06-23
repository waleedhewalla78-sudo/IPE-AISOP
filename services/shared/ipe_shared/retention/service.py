"""Data retention enforcement service (P9-009).

Applies configured retention policies: archive, anonymize, or delete rows
older than the retention period. All operations are audit-logged.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import text

from ipe_shared.audit.service import log_audit_event
from ipe_shared.retention.config import get_retention_policy

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

PII_COLUMNS: dict[str, list[str]] = {
    "cdm_mdr_score": ["customer_id", "product_id"],
    "cdm_user": ["email", "full_name"],
    "cdm_customer": ["name", "email"],
    "cdm_supplier": ["name", "contact_email"],
}


class RetentionService:
    async def enforce_retention(
        self,
        session: AsyncSession,
        entity_type: str,
        tenant_id: UUID | str | None = None,
    ) -> dict:
        policy = get_retention_policy(entity_type)
        if policy is None:
            logger.warning(
                "No retention policy for entity_type=%s", entity_type,
            )
            return {
                "entity_type": entity_type,
                "rows_affected": 0,
                "action": "none",
                "error": "no_policy",
            }

        cutoff_date = datetime.now(UTC) - timedelta(days=policy.retention_days)
        result: dict = {
            "entity_type": entity_type,
            "rows_affected": 0,
            "action": policy.action,
        }

        if policy.action == "archive":
            rows = await self.archive_then_delete(
                session,
                policy.entity_type,
                cutoff_date,
                policy.archive_table,
                tenant_id=tenant_id,
            )
            result["rows_affected"] = rows
        elif policy.action == "anonymize":
            pii_cols = PII_COLUMNS.get(policy.entity_type, [])
            rows = await self.anonymize_rows(
                session,
                policy.entity_type,
                cutoff_date,
                pii_cols,
                tenant_id=tenant_id,
            )
            result["rows_affected"] = rows
        elif policy.action == "delete":
            rows = await self.delete_expired(
                session,
                policy.entity_type,
                cutoff_date,
                tenant_id=tenant_id,
            )
            result["rows_affected"] = rows

        await log_audit_event(
            tenant_id=tenant_id or "system",
            actor_type="system",
            actor_id="retention_service",
            action="RETENTION_ENFORCE",
            entity_type=entity_type,
            entity_id="batch",
            after_state={
                "action": policy.action,
                "rows_affected": result["rows_affected"],
                "cutoff_date": cutoff_date.isoformat(),
            },
            rationale=(
                f"Applied {policy.action} retention policy "
                f"({policy.retention_days} days)"
            ),
        )

        return result

    async def archive_then_delete(
        self,
        session: AsyncSession,
        table: str,
        cutoff_date: datetime,
        archive_table: str | None,
        tenant_id: UUID | str | None = None,
    ) -> int:
        if archive_table is None:
            archive_table = f"{table}_archive"

        params: dict = {"cutoff": cutoff_date}
        if tenant_id:
            params["tid"] = str(tenant_id)

        if tenant_id:
            insert_sql = text(
                f"INSERT INTO {archive_table} SELECT * FROM {table} "
                f"WHERE timestamp < :cutoff AND tenant_id = :tid",
            )
        else:
            insert_sql = text(
                f"INSERT INTO {archive_table} SELECT * FROM {table} "
                f"WHERE timestamp < :cutoff",
            )

        await session.execute(insert_sql, params)

        if tenant_id:
            delete_sql = text(
                f"DELETE FROM {table} "
                f"WHERE timestamp < :cutoff AND tenant_id = :tid",
            )
        else:
            delete_sql = text(
                f"DELETE FROM {table} WHERE timestamp < :cutoff",
            )

        result = await session.execute(delete_sql, params)
        await session.commit()
        count = result.rowcount
        logger.info(
            "Archived %d rows from %s to %s", count, table, archive_table,
        )
        return count

    async def anonymize_rows(
        self,
        session: AsyncSession,
        table: str,
        cutoff_date: datetime,
        pii_columns: list[str],
        tenant_id: UUID | str | None = None,
    ) -> int:
        if not pii_columns:
            logger.warning(
                "No PII columns to anonymize for %s, skipping", table,
            )
            return 0

        set_clauses = ", ".join(
            f"{col} = '[ANONYMIZED]'" for col in pii_columns
        )
        sql_str = (
            f"UPDATE {table} SET {set_clauses} "
            f"WHERE timestamp < :cutoff"
        )
        if tenant_id:
            sql_str += " AND tenant_id = :tid"

        params: dict = {"cutoff": cutoff_date}
        if tenant_id:
            params["tid"] = str(tenant_id)

        result = await session.execute(text(sql_str), params)
        await session.commit()
        count = result.rowcount
        logger.info("Anonymized %d rows in %s", count, table)
        return count

    async def delete_expired(
        self,
        session: AsyncSession,
        table: str,
        cutoff_date: datetime,
        tenant_id: UUID | str | None = None,
    ) -> int:
        sql_str = f"DELETE FROM {table} WHERE timestamp < :cutoff"
        if tenant_id:
            sql_str += " AND tenant_id = :tid"

        params: dict = {"cutoff": cutoff_date}
        if tenant_id:
            params["tid"] = str(tenant_id)

        result = await session.execute(text(sql_str), params)
        await session.commit()
        count = result.rowcount
        logger.info("Deleted %d expired rows from %s", count, table)
        return count
