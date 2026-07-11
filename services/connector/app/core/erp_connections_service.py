"""ERP connection CRUD, test, activate, sync-now (W1-04)."""

from __future__ import annotations

import asyncio
import logging
import socket
import time
import xmlrpc.client
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.erp_connection import ErpConnection, ErpConnectionLog

from app.core.password_crypto import decrypt_password, encrypt_password
from app.schemas.erp_connections import (
    ErpConnectionCreate,
    ErpConnectionResponse,
    ErpConnectionUpdate,
)

logger = logging.getLogger(__name__)

CONNECTION_TIMEOUT_SECONDS = 10.0


def to_response(row: ErpConnection) -> ErpConnectionResponse:
    return ErpConnectionResponse(
        id=row.id,
        display_name=row.display_name,
        host_url=row.host_url,
        database_name=row.database_name,
        username=row.username,
        erp_type=row.erp_type,
        is_active=bool(row.is_active),
        is_production=bool(row.is_production),
        last_test_at=row.last_test_at,
        last_test_result=row.last_test_result,
        last_test_message=row.last_test_message,
        sync_interval_seconds=int(row.sync_interval_seconds or 900),
        sync_enabled=bool(row.sync_enabled),
        api_protocol=row.api_protocol or "xmlrpc",
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def _add_log(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    connection_id: UUID,
    action: str,
    result: str | None = None,
    details: dict[str, Any] | None = None,
    performed_by: UUID | None = None,
) -> None:
    session.add(
        ErpConnectionLog(
            tenant_id=tenant_id,
            connection_id=connection_id,
            action=action,
            result=result,
            details=details,
            performed_by=performed_by,
        )
    )


async def list_connections(session: AsyncSession, tenant_id: UUID) -> list[ErpConnectionResponse]:
    result = await session.execute(
        select(ErpConnection)
        .where(ErpConnection.tenant_id == tenant_id)
        .order_by(desc(ErpConnection.is_active), ErpConnection.display_name)
    )
    return [to_response(r) for r in result.scalars().all()]


async def get_connection(
    session: AsyncSession, tenant_id: UUID, connection_id: UUID
) -> ErpConnection:
    row = (
        await session.execute(
            select(ErpConnection).where(
                and_(ErpConnection.id == connection_id, ErpConnection.tenant_id == tenant_id)
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "ERP connection not found"},
        )
    return row


async def create_connection(
    session: AsyncSession,
    tenant_id: UUID,
    req: ErpConnectionCreate,
    *,
    created_by: UUID | None = None,
) -> ErpConnectionResponse:
    # New connections start inactive if another active exists for same type
    existing_active = (
        await session.execute(
            select(ErpConnection).where(
                and_(
                    ErpConnection.tenant_id == tenant_id,
                    ErpConnection.erp_type == req.erp_type,
                    ErpConnection.is_active.is_(True),
                )
            )
        )
    ).scalar_one_or_none()

    row = ErpConnection(
        tenant_id=tenant_id,
        erp_type=req.erp_type,
        display_name=req.display_name,
        host_url=req.host_url,
        database_name=req.database_name,
        username=req.username,
        password_encrypted=encrypt_password(req.password),
        api_protocol=req.api_protocol,
        is_active=existing_active is None,
        is_production=req.is_production,
        sync_interval_seconds=req.sync_interval_seconds,
        sync_enabled=req.sync_enabled,
        created_by=created_by,
    )
    session.add(row)
    await session.flush()
    await _add_log(
        session,
        tenant_id=tenant_id,
        connection_id=row.id,
        action="config_change",
        result="success",
        details={"event": "created", "display_name": req.display_name},
        performed_by=created_by,
    )
    await session.commit()
    await session.refresh(row)
    return to_response(row)


async def update_connection(
    session: AsyncSession,
    tenant_id: UUID,
    connection_id: UUID,
    req: ErpConnectionUpdate,
    *,
    performed_by: UUID | None = None,
) -> ErpConnectionResponse:
    row = await get_connection(session, tenant_id, connection_id)
    changes: dict[str, Any] = {}
    data = req.model_dump(exclude_unset=True)
    password = data.pop("password", None)
    for key, value in data.items():
        setattr(row, key, value)
        changes[key] = value
    if password:
        row.password_encrypted = encrypt_password(password)
        changes["password"] = "***"
    row.updated_at = datetime.now(UTC)
    await _add_log(
        session,
        tenant_id=tenant_id,
        connection_id=row.id,
        action="config_change",
        result="success",
        details={"changes": changes},
        performed_by=performed_by,
    )
    await session.commit()
    await session.refresh(row)
    return to_response(row)


async def soft_delete_connection(
    session: AsyncSession,
    tenant_id: UUID,
    connection_id: UUID,
    *,
    performed_by: UUID | None = None,
) -> None:
    row = await get_connection(session, tenant_id, connection_id)
    row.is_active = False
    row.updated_at = datetime.now(UTC)
    await _add_log(
        session,
        tenant_id=tenant_id,
        connection_id=row.id,
        action="deactivate",
        result="success",
        details={"event": "soft_delete"},
        performed_by=performed_by,
    )
    await session.commit()


def _probe_odoo(url: str, db: str, user: str, password: str) -> dict[str, Any]:
    """Synchronous XML-RPC probe: version → db.list → authenticate."""
    common = xmlrpc.client.ServerProxy(f"{url.rstrip('/')}/xmlrpc/2/common", allow_none=True)
    version_info = common.version()
    odoo_version = None
    if isinstance(version_info, dict):
        odoo_version = version_info.get("server_version") or str(version_info)
    else:
        odoo_version = str(version_info)

    databases: list[str] | None = None
    try:
        db_proxy = xmlrpc.client.ServerProxy(f"{url.rstrip('/')}/xmlrpc/2/db", allow_none=True)
        listed = db_proxy.list()
        if isinstance(listed, list):
            databases = [str(x) for x in listed]
    except Exception:
        databases = None

    uid = common.authenticate(db, user, password, {})
    if not uid:
        return {
            "result": "auth_failed",
            "message": "Authentication failed — check username/password/database",
            "odoo_version": odoo_version,
            "databases_available": databases,
        }
    return {
        "result": "success",
        "message": "Connection successful",
        "odoo_version": odoo_version,
        "databases_available": databases,
        "uid": int(uid),
    }


async def test_connection(
    session: AsyncSession,
    tenant_id: UUID,
    connection_id: UUID,
    *,
    performed_by: UUID | None = None,
) -> dict[str, Any]:
    row = await get_connection(session, tenant_id, connection_id)
    try:
        password = decrypt_password(row.password_encrypted)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "DECRYPT_FAILED", "message": str(exc)},
        ) from exc

    started = time.perf_counter()
    try:
        outcome = await asyncio.wait_for(
            asyncio.to_thread(
                _probe_odoo, row.host_url, row.database_name, row.username, password
            ),
            timeout=CONNECTION_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        outcome = {
            "result": "timeout",
            "message": f"Connection exceeded {CONNECTION_TIMEOUT_SECONDS}s",
            "odoo_version": None,
            "databases_available": None,
        }
    except (OSError, socket.error, ConnectionError) as exc:
        outcome = {
            "result": "unreachable",
            "message": f"Host unreachable: {exc}",
            "odoo_version": None,
            "databases_available": None,
        }
    except xmlrpc.client.ProtocolError as exc:
        outcome = {
            "result": "unreachable",
            "message": f"Protocol error: {exc}",
            "odoo_version": None,
            "databases_available": None,
        }
    except Exception as exc:
        msg = str(exc).lower()
        if "auth" in msg or "access denied" in msg:
            outcome = {
                "result": "auth_failed",
                "message": str(exc),
                "odoo_version": None,
                "databases_available": None,
            }
        else:
            outcome = {
                "result": "unreachable",
                "message": str(exc),
                "odoo_version": None,
                "databases_available": None,
            }

    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
    row.last_test_at = datetime.now(UTC)
    row.last_test_result = outcome["result"]
    row.last_test_message = outcome["message"]
    row.updated_at = datetime.now(UTC)
    await _add_log(
        session,
        tenant_id=tenant_id,
        connection_id=row.id,
        action="test",
        result=outcome["result"],
        details={**outcome, "response_time_ms": elapsed_ms},
        performed_by=performed_by,
    )
    await session.commit()
    return {
        "result": outcome["result"],
        "message": outcome["message"],
        "response_time_ms": elapsed_ms,
        "odoo_version": outcome.get("odoo_version"),
        "databases_available": outcome.get("databases_available"),
    }


async def activate_connection(
    session: AsyncSession,
    tenant_id: UUID,
    connection_id: UUID,
    *,
    performed_by: UUID | None = None,
) -> ErpConnectionResponse:
    row = await get_connection(session, tenant_id, connection_id)
    await session.execute(
        update(ErpConnection)
        .where(
            and_(
                ErpConnection.tenant_id == tenant_id,
                ErpConnection.erp_type == row.erp_type,
                ErpConnection.is_active.is_(True),
                ErpConnection.id != row.id,
            )
        )
        .values(is_active=False, updated_at=datetime.now(UTC))
    )
    row.is_active = True
    row.updated_at = datetime.now(UTC)
    await _add_log(
        session,
        tenant_id=tenant_id,
        connection_id=row.id,
        action="activate",
        result="success",
        details={"erp_type": row.erp_type},
        performed_by=performed_by,
    )
    await session.commit()
    await session.refresh(row)
    return to_response(row)


async def list_logs(
    session: AsyncSession,
    tenant_id: UUID,
    connection_id: UUID,
    *,
    limit: int = 20,
    action: str | None = None,
) -> list[ErpConnectionLog]:
    await get_connection(session, tenant_id, connection_id)
    stmt = (
        select(ErpConnectionLog)
        .where(
            and_(
                ErpConnectionLog.tenant_id == tenant_id,
                ErpConnectionLog.connection_id == connection_id,
            )
        )
        .order_by(desc(ErpConnectionLog.performed_at))
        .limit(min(limit, 100))
    )
    if action:
        stmt = stmt.where(ErpConnectionLog.action == action)
    return list((await session.execute(stmt)).scalars().all())


async def sync_now(
    session: AsyncSession,
    tenant_id: UUID,
    connection_id: UUID,
    *,
    performed_by: UUID | None = None,
) -> dict[str, Any]:
    row = await get_connection(session, tenant_id, connection_id)
    if not row.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INACTIVE", "message": "Activate the connection before syncing"},
        )
    sync_run_id = str(uuid4())
    await _add_log(
        session,
        tenant_id=tenant_id,
        connection_id=row.id,
        action="sync_schedule_change",
        result="success",
        details={"event": "sync_now", "sync_run_id": sync_run_id},
        performed_by=performed_by,
    )
    await session.commit()

    # Best-effort trigger of existing Odoo sync engine
    try:
        from app.odoo.sync_engine import OdooSyncEngine

        engine = OdooSyncEngine()
        if hasattr(engine, "trigger_sync"):
            await engine.trigger_sync(str(tenant_id), sync_run_id=sync_run_id)
        elif hasattr(engine, "run_sync"):
            asyncio.create_task(engine.run_sync(str(tenant_id)))
    except Exception:
        logger.exception("sync-now: could not start sync engine (logged run id %s)", sync_run_id)

    return {"sync_run_id": sync_run_id, "status": "started"}
