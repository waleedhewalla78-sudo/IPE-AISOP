"""Odoo Config v2 persistence and versioning (W1-03–05)."""

from __future__ import annotations

import asyncio
import logging
import time
import xmlrpc.client
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.integrations.odoo_credentials import (
    decrypt_odoo_password,
    encrypt_odoo_password,
    odoo_password_is_set,
)
from ipe_shared.models.odoo_config_version import OdooConfigVersion
from ipe_shared.models.tenant import Tenant

from app.schemas.odoo_config_v2 import (
    DEFAULT_FIELD_MAPPINGS,
    OdooConfigCreateRequest,
    OdooConfigTestRequest,
    OdooConfigVersionSummary,
    validate_field_mappings,
)

logger = logging.getLogger(__name__)

CONNECTION_TIMEOUT_SECONDS = 5.0


def _serialize_mappings(row: OdooConfigVersion) -> dict[str, list[dict[str, Any]]]:
    raw = row.field_mappings or {}
    return {k: list(v) if isinstance(v, list) else [] for k, v in raw.items()}


def _to_summary(row: OdooConfigVersion) -> OdooConfigVersionSummary:
    return OdooConfigVersionSummary(
        entity_key=row.entity_key,
        version=row.version,
        is_current=row.is_current,
        name=row.name or "",
        odoo_url=row.odoo_url,
        odoo_db=row.odoo_db,
        odoo_username=row.odoo_username,
        enabled=row.enabled,
        sync_interval_minutes=row.sync_interval_minutes,
        password_set=bool(row.odoo_password_enc),
        field_mappings=_serialize_mappings(row),
        change_summary=row.change_summary,
        created_at=row.created_at.isoformat() if row.created_at else None,
    )


def _cfg_dict_from_row(row: OdooConfigVersion) -> dict[str, Any]:
    return {
        "odoo_url": row.odoo_url,
        "odoo_db": row.odoo_db,
        "odoo_username": row.odoo_username,
        "odoo_password_enc": row.odoo_password_enc,
        "odoo_enabled": row.enabled,
    }


async def _sync_tenant_legacy_config(session: AsyncSession, tenant: Tenant, row: OdooConfigVersion) -> None:
    """Keep tenant.config backward-compatible for v1 sync paths."""
    cfg = dict(tenant.config or {})
    cfg.update(
        {
            "odoo_url": row.odoo_url,
            "odoo_db": row.odoo_db,
            "odoo_username": row.odoo_username,
            "odoo_enabled": row.enabled,
            "odoo_config_v2_entity": row.entity_key,
            "odoo_config_v2_version": row.version,
        }
    )
    if row.odoo_password_enc:
        cfg["odoo_password_enc"] = row.odoo_password_enc
        cfg.pop("odoo_password", None)
    tenant.erp_type = "odoo"
    tenant.erp_base_url = row.odoo_url
    tenant.config = cfg


async def bootstrap_v1_from_tenant(
    session: AsyncSession, tenant: Tenant, entity_key: str = "primary"
) -> OdooConfigVersion | None:
    cfg = dict(tenant.config or {})
    url = tenant.erp_base_url or cfg.get("odoo_url")
    db = cfg.get("odoo_db")
    user = cfg.get("odoo_username")
    if not all([url, db, user]):
        return None

    enc = cfg.get("odoo_password_enc")
    row = OdooConfigVersion(
        tenant_id=tenant.id,
        entity_key=entity_key,
        version=1,
        is_current=True,
        name=cfg.get("odoo_instance_name") or "Primary Odoo",
        odoo_url=str(url).rstrip("/"),
        odoo_db=str(db),
        odoo_username=str(user),
        odoo_password_enc=enc,
        enabled=bool(cfg.get("odoo_enabled", True)),
        sync_interval_minutes=int(cfg.get("odoo_sync_interval_minutes", 900)),
        field_mappings=DEFAULT_FIELD_MAPPINGS,
        change_summary="Bootstrapped from v1 tenant.config",
    )
    session.add(row)
    await session.flush()
    return row


async def list_current_configs(
    session: AsyncSession, tenant_id: UUID, *, bootstrap: bool = True
) -> list[OdooConfigVersionSummary]:
    result = await session.execute(
        select(OdooConfigVersion)
        .where(and_(OdooConfigVersion.tenant_id == tenant_id, OdooConfigVersion.is_current.is_(True)))
        .order_by(OdooConfigVersion.entity_key)
    )
    rows = list(result.scalars().all())
    if not rows and bootstrap:
        tenant = (
            await session.execute(select(Tenant).where(Tenant.id == tenant_id))
        ).scalar_one_or_none()
        if tenant:
            boot = await bootstrap_v1_from_tenant(session, tenant)
            if boot:
                rows = [boot]
                await session.commit()
    return [_to_summary(r) for r in rows]


async def get_current_config(
    session: AsyncSession, tenant_id: UUID, entity_key: str
) -> OdooConfigVersion | None:
    result = await session.execute(
        select(OdooConfigVersion).where(
            and_(
                OdooConfigVersion.tenant_id == tenant_id,
                OdooConfigVersion.entity_key == entity_key,
                OdooConfigVersion.is_current.is_(True),
            )
        )
    )
    row = result.scalar_one_or_none()
    if row:
        return row

    if entity_key == "primary":
        tenant = (
            await session.execute(select(Tenant).where(Tenant.id == tenant_id))
        ).scalar_one_or_none()
        if tenant:
            boot = await bootstrap_v1_from_tenant(session, tenant, entity_key)
            if boot:
                await session.commit()
                await session.refresh(boot)
                return boot
    return None


async def list_versions(
    session: AsyncSession, tenant_id: UUID, entity_key: str
) -> list[OdooConfigVersionSummary]:
    result = await session.execute(
        select(OdooConfigVersion)
        .where(
            and_(
                OdooConfigVersion.tenant_id == tenant_id,
                OdooConfigVersion.entity_key == entity_key,
            )
        )
        .order_by(desc(OdooConfigVersion.version))
    )
    return [_to_summary(r) for r in result.scalars().all()]


async def create_config_version(
    session: AsyncSession,
    tenant_id: UUID,
    req: OdooConfigCreateRequest,
    *,
    created_by: UUID | None = None,
) -> OdooConfigVersionSummary:
    current = await get_current_config(session, tenant_id, req.entity_key)
    next_version = (current.version + 1) if current else 1

    if req.expected_version is not None and current and req.expected_version != current.version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "VERSION_CONFLICT",
                "message": f"Expected version {req.expected_version}, current is {current.version}",
                "current_version": current.version,
            },
        )

    mappings = {
        entity: [item.model_dump() for item in items] for entity, items in req.field_mappings.items()
    }
    validate_field_mappings(mappings)

    password_enc = None
    if req.odoo_password:
        password_enc = encrypt_odoo_password(req.odoo_password)
    elif current and current.odoo_password_enc:
        password_enc = current.odoo_password_enc
    elif not current:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "PASSWORD_REQUIRED", "message": "odoo_password required for new entity"},
        )

    if current:
        await session.execute(
            update(OdooConfigVersion)
            .where(
                and_(
                    OdooConfigVersion.tenant_id == tenant_id,
                    OdooConfigVersion.entity_key == req.entity_key,
                    OdooConfigVersion.is_current.is_(True),
                )
            )
            .values(is_current=False)
        )

    row = OdooConfigVersion(
        tenant_id=tenant_id,
        entity_key=req.entity_key,
        version=next_version,
        is_current=True,
        name=req.name or (current.name if current else req.entity_key),
        odoo_url=req.odoo_url,
        odoo_db=req.odoo_db,
        odoo_username=req.odoo_username,
        odoo_password_enc=password_enc,
        enabled=req.enabled,
        sync_interval_minutes=req.sync_interval_minutes,
        field_mappings=mappings,
        change_summary=req.change_summary,
        created_by=created_by,
    )
    session.add(row)
    await session.flush()

    tenant = (
        await session.execute(select(Tenant).where(Tenant.id == tenant_id))
    ).scalar_one_or_none()
    if tenant and req.entity_key == "primary":
        await _sync_tenant_legacy_config(session, tenant, row)

    await session.commit()
    await session.refresh(row)
    return _to_summary(row)


async def rollback_config(
    session: AsyncSession, tenant_id: UUID, entity_key: str, target_version: int
) -> OdooConfigVersionSummary:
    result = await session.execute(
        select(OdooConfigVersion).where(
            and_(
                OdooConfigVersion.tenant_id == tenant_id,
                OdooConfigVersion.entity_key == entity_key,
                OdooConfigVersion.version == target_version,
            )
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "VERSION_NOT_FOUND", "message": f"Version {target_version} not found"},
        )

    req = OdooConfigCreateRequest(
        entity_key=entity_key,
        name=source.name,
        odoo_url=source.odoo_url,
        odoo_db=source.odoo_db,
        odoo_username=source.odoo_username,
        enabled=source.enabled,
        sync_interval_minutes=source.sync_interval_minutes,
        field_mappings={
            k: [{"ipe_field": i["ipe_field"], "odoo_model": i["odoo_model"], "odoo_field": i["odoo_field"], "transform": i.get("transform")}
                for i in v]
            for k, v in _serialize_mappings(source).items()
        },
        change_summary=f"Rollback to version {target_version}",
    )
    return await create_config_version(session, tenant_id, req)


def _authenticate_odoo(url: str, db: str, user: str, password: str) -> tuple[int, dict]:
    common = xmlrpc.client.ServerProxy(f"{url.rstrip('/')}/xmlrpc/2/common", allow_none=True)
    uid = common.authenticate(db, user, password, {})
    if not uid:
        raise ConnectionError("Odoo authentication failed")
    version = common.version()
    return int(uid), version


async def test_odoo_connection(
    session: AsyncSession,
    tenant_id: UUID,
    req: OdooConfigTestRequest,
) -> dict[str, Any]:
    url = req.odoo_url
    db = req.odoo_db
    user = req.odoo_username
    password = req.odoo_password

    if req.entity_key:
        row = await get_current_config(session, tenant_id, req.entity_key)
        if row:
            url = url or row.odoo_url
            db = db or row.odoo_db
            user = user or row.odoo_username
            if not password and row.odoo_password_enc:
                password = decrypt_odoo_password(_cfg_dict_from_row(row))

    if not password:
        tenant = (
            await session.execute(select(Tenant).where(Tenant.id == tenant_id))
        ).scalar_one_or_none()
        if tenant:
            password = decrypt_odoo_password(tenant.config or {})

    if not all([url, db, user, password]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "INCOMPLETE_CONFIG",
                "message": "Odoo URL, DB, username, and password required",
            },
        )

    started = time.perf_counter()
    try:
        uid, version_info = await asyncio.wait_for(
            asyncio.to_thread(_authenticate_odoo, str(url), str(db), str(user), str(password)),
            timeout=CONNECTION_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"code": "CONNECTION_TIMEOUT", "message": "Odoo connection exceeded 5s SLA"},
        ) from None
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "CONNECTION_FAILED", "message": str(exc)},
        ) from exc

    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    return {
        "connected": True,
        "uid": uid,
        "server_version": version_info.get("server_version"),
        "latency_ms": latency_ms,
        "entity_key": req.entity_key,
    }


def v1_compat_password_set(tenant: Tenant | None) -> bool:
    if not tenant:
        return False
    return odoo_password_is_set(tenant.config or {})
