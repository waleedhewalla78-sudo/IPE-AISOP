from uuid import UUID
import xmlrpc.client

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel
from sqlalchemy import select as sa_select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session
from ipe_shared.integrations.odoo_credentials import (
    decrypt_odoo_password,
    odoo_password_is_set,
    store_odoo_password,
)
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.tenant import Tenant
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/admin", tags=["admin"])


class ConfigUpdate(BaseModel):
    priority_weights: dict[str, float] | None = None
    strategic_product_ids: list[str] | None = None
    feasibility_thresholds: dict[str, float] | None = None
    autonomy_mode: str | None = None


class OdooConfigUpdate(BaseModel):
    odoo_url: str | None = None
    odoo_db: str | None = None
    odoo_username: str | None = None
    odoo_password: str | None = None
    enabled: bool | None = None


@router.put("/config")
async def update_config(
    req: ConfigUpdate,
    current_user=Depends(require_roles(["admin"])),
    session: AsyncSession = Depends(get_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    result = await session.execute(
        sa_select(Tenant).where(Tenant.id == UUID(tenant_id))
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        return APIResponse(
            success=False, data=None,
            error={"code": "NOT_FOUND", "message": "Tenant not found"},
        )

    current_config = dict(tenant.config or {})

    if req.priority_weights is not None:
        priority_config = current_config.get("priority_weights", {})
        priority_config.update(req.priority_weights)
        current_config["priority_weights"] = priority_config

    if req.strategic_product_ids is not None:
        current_config["strategic_product_ids"] = req.strategic_product_ids

    if req.feasibility_thresholds is not None:
        thresholds = current_config.get("feasibility_thresholds", {})
        thresholds.update(req.feasibility_thresholds)
        current_config["feasibility_thresholds"] = thresholds

    tenant.config = current_config

    if req.autonomy_mode is not None:
        tenant.autonomy_mode = req.autonomy_mode

    await session.commit()

    return APIResponse(
        success=True,
        data={
            "config": current_config,
            "autonomy_mode": tenant.autonomy_mode,
        },
        error=None,
    )


@router.get("/config")
async def get_config(
    session: AsyncSession = Depends(get_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    result = await session.execute(
        sa_select(Tenant).where(Tenant.id == UUID(tenant_id))
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        return APIResponse(
            success=False, data=None,
            error={"code": "NOT_FOUND", "message": "Tenant not found"},
        )

    return APIResponse(
        success=True,
        data={
            "config": tenant.config or {},
            "autonomy_mode": tenant.autonomy_mode,
            "erp_type": tenant.erp_type,
            "erp_base_url": tenant.erp_base_url,
        },
        error=None,
    )


def _mask_odoo_config(cfg: dict) -> dict:
    out = {
        "odoo_url": cfg.get("odoo_url") or "",
        "odoo_db": cfg.get("odoo_db") or "",
        "odoo_username": cfg.get("odoo_username") or "",
        "enabled": bool(cfg.get("odoo_enabled", True)),
        "password_set": odoo_password_is_set(cfg),
    }
    return out


@router.get("/erp/odoo")
async def get_odoo_config(
    session: AsyncSession = Depends(get_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    result = await session.execute(
        sa_select(Tenant).where(Tenant.id == UUID(tenant_id))
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        return APIResponse(
            success=False, data=None,
            error={"code": "NOT_FOUND", "message": "Tenant not found"},
        )

    cfg = dict(tenant.config or {})
    if tenant.erp_base_url and not cfg.get("odoo_url"):
        cfg["odoo_url"] = tenant.erp_base_url

    return APIResponse(
        success=True,
        data={
            "erp_type": tenant.erp_type,
            **_mask_odoo_config(cfg),
        },
        error=None,
    )


@router.put("/erp/odoo")
async def update_odoo_config(
    req: OdooConfigUpdate,
    current_user=Depends(require_roles(["admin"])),
    session: AsyncSession = Depends(get_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    result = await session.execute(
        sa_select(Tenant).where(Tenant.id == UUID(tenant_id))
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        return APIResponse(
            success=False, data=None,
            error={"code": "NOT_FOUND", "message": "Tenant not found"},
        )

    cfg = dict(tenant.config or {})
    if req.odoo_url is not None:
        cfg["odoo_url"] = req.odoo_url.rstrip("/")
        tenant.erp_base_url = cfg["odoo_url"]
    if req.odoo_db is not None:
        cfg["odoo_db"] = req.odoo_db
    if req.odoo_username is not None:
        cfg["odoo_username"] = req.odoo_username
    if req.odoo_password is not None and req.odoo_password:
        cfg = store_odoo_password(cfg, req.odoo_password)
    if req.enabled is not None:
        cfg["odoo_enabled"] = req.enabled

    tenant.erp_type = "odoo"
    tenant.config = cfg
    await session.commit()

    return APIResponse(
        success=True,
        data={"erp_type": tenant.erp_type, **_mask_odoo_config(cfg)},
        error=None,
    )


@router.post("/erp/odoo/test")
async def test_odoo_connection(
    req: OdooConfigUpdate = Body(default_factory=OdooConfigUpdate),
    current_user=Depends(require_roles(["admin"])),
    session: AsyncSession = Depends(get_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    result = await session.execute(
        sa_select(Tenant).where(Tenant.id == UUID(tenant_id))
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        return APIResponse(
            success=False, data=None,
            error={"code": "NOT_FOUND", "message": "Tenant not found"},
        )

    cfg = dict(tenant.config or {})
    url = req.odoo_url or tenant.erp_base_url or cfg.get("odoo_url")
    db = req.odoo_db or cfg.get("odoo_db")
    user = req.odoo_username or cfg.get("odoo_username")
    password = req.odoo_password or decrypt_odoo_password(cfg)

    if not all([url, db, user, password]):
        return APIResponse(
            success=False,
            data=None,
            error={"code": "INCOMPLETE_CONFIG", "message": "Odoo URL, DB, username, and password required"},
        )

    try:
        common = xmlrpc.client.ServerProxy(f"{url.rstrip('/')}/xmlrpc/2/common", allow_none=True)
        uid = common.authenticate(db, user, password, {})
        if not uid:
            return APIResponse(
                success=False,
                data={"connected": False},
                error={"code": "AUTH_FAILED", "message": "Odoo authentication failed"},
            )
        version = common.version()
        return APIResponse(
            success=True,
            data={"connected": True, "uid": uid, "server_version": version.get("server_version")},
            error=None,
        )
    except Exception as exc:
        return APIResponse(
            success=False,
            data={"connected": False},
            error={"code": "CONNECTION_FAILED", "message": str(exc)},
        )


@router.get("/data-quality")
async def get_data_quality(
    session: AsyncSession = Depends(get_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    tid = UUID(tenant_id)

    total_boms_query = await session.execute(
        text("SELECT COUNT(*) FROM cdm_bill_of_material WHERE tenant_id = :tid"),
        {"tid": tid},
    )
    total_boms = total_boms_query.scalar() or 0

    complete_boms_query = await session.execute(
        text("""
            SELECT COUNT(*) FROM cdm_bill_of_material b
            WHERE b.tenant_id = :tid
            AND EXISTS (
                SELECT 1 FROM cdm_bom_line bl
                WHERE bl.bom_id = b.id
            )
        """),
        {"tid": tid},
    )
    complete_boms = complete_boms_query.scalar() or 0
    bom_completeness_pct = round(
        (complete_boms / total_boms) * 100, 1
    ) if total_boms > 0 else 100.0

    wo_query = await session.execute(
        text("""
            SELECT COUNT(*),
                   COUNT(*) FILTER (
                       WHERE duration_actual_mins IS NOT NULL
                       AND ABS(duration_actual_mins - duration_planned_mins)
                       / NULLIF(duration_planned_mins, 0) <= 0.15
                   ) AS accurate_count
            FROM cdm_work_order
            WHERE tenant_id = :tid
        """),
        {"tid": tid},
    )
    wo_row = wo_query.one()
    total_wos = wo_row[0] or 0
    accurate_wos = wo_row[1] or 0
    lead_time_accuracy_pct = round(
        (accurate_wos / total_wos) * 100, 1
    ) if total_wos > 0 else 100.0

    inv_query = await session.execute(
        text("""
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (
                       WHERE safety_stock IS NOT NULL AND safety_stock > 0
                   ) AS with_stock
            FROM cdm_product
            WHERE tenant_id = :tid AND source_type = 'manufactured'
        """),
        {"tid": tid},
    )
    inv_row = inv_query.one()
    total_products = inv_row[0] or 0
    products_with_stock = inv_row[1] or 0
    inventory_record_accuracy_pct = round(
        (products_with_stock / total_products) * 100, 1
    ) if total_products > 0 else 100.0

    return APIResponse(
        success=True,
        data={
            "bom_completeness_pct": bom_completeness_pct,
            "lead_time_accuracy_pct": lead_time_accuracy_pct,
            "inventory_record_accuracy_pct": inventory_record_accuracy_pct,
        },
        error=None,
    )
