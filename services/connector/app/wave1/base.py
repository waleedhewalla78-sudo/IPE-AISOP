"""Wave 1 read-only Odoo → cdm_ingest_* adapters."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

logger = logging.getLogger(__name__)

STAR_TRANS_TENANT = UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")


class OdooFetchClient(Protocol):
    def authenticate(self) -> int: ...
    def search_read(
        self,
        model: str,
        domain: list | None = None,
        fields: list[str] | None = None,
        limit: int | None = None,
    ) -> list[dict]: ...


@dataclass
class CanonicalRecord:
    table: str
    natural_key: str
    fields: dict[str, Any]
    source_id: str
    payload: dict[str, Any]


@dataclass
class UpsertResult:
    key: str
    ok: bool
    error: str | None = None


@dataclass
class AdapterResult:
    entity: str
    fetched: int = 0
    upserted: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


def _m2o_name(value: Any) -> str | None:
    if value is None or value is False:
        return None
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return str(value[1])
    return str(value)


def _m2o_id(value: Any) -> str | None:
    if value is None or value is False:
        return None
    if isinstance(value, (list, tuple)) and value:
        return str(value[0])
    return str(value)


class BaseAdapter:
    entity: str = ""
    odoo_model: str = ""
    ingest_table: str = ""
    odoo_fields: list[str] = []
    domain: list = []
    nk_field: str = "id"

    def __init__(self, client: OdooFetchClient, store: dict[tuple[str, str], CanonicalRecord] | None = None):
        self.client = client
        self.store = store if store is not None else {}

    def fetch_from_odoo(self, since: datetime | None = None) -> list[dict]:
        domain = list(self.domain)
        if since:
            domain = domain + [["write_date", ">=", since.strftime("%Y-%m-%d %H:%M:%S")]]
        rows = self.client.search_read(self.odoo_model, domain, self.odoo_fields or None, 500)
        logger.info("wave1_fetch", extra={"entity": self.entity, "count": len(rows)})
        return rows

    def transform_to_canonical(self, odoo_record: dict) -> CanonicalRecord | None:
        raise NotImplementedError

    def upsert_to_ipe(self, record: CanonicalRecord) -> UpsertResult:
        key = (record.table, record.natural_key)
        self.store[key] = record
        return UpsertResult(key=record.natural_key, ok=True)

    def run(self, since: datetime | None = None) -> AdapterResult:
        result = AdapterResult(entity=self.entity)
        try:
            raw = self.fetch_from_odoo(since)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(str(exc))
            result.failed = 1
            return result
        result.fetched = len(raw)
        for row in raw:
            try:
                canon = self.transform_to_canonical(row)
                if canon is None:
                    continue
                up = self.upsert_to_ipe(canon)
                if up.ok:
                    result.upserted += 1
                else:
                    result.failed += 1
                    result.errors.append(up.error or "upsert failed")
            except Exception as exc:  # noqa: BLE001
                result.failed += 1
                result.errors.append(str(exc))
        return result


class PlantAdapter(BaseAdapter):
    entity = "plants"
    odoo_model = "stock.warehouse"
    ingest_table = "cdm_ingest_plant"
    odoo_fields = ["id", "name", "code", "company_id"]

    def transform_to_canonical(self, odoo_record: dict) -> CanonicalRecord | None:
        oid = str(odoo_record.get("id"))
        code = odoo_record.get("code") or f"WH-{oid}"
        return CanonicalRecord(
            table=self.ingest_table,
            natural_key=code,
            fields={"name": odoo_record.get("name") or code},
            source_id=oid,
            payload={
                **{k: v for k, v in odoo_record.items() if v not in (None, False)},
                "source_system": "odoo",
                "source_id": oid,
                "synced_at": datetime.now(UTC).isoformat(),
            },
        )


class WorkCenterAdapter(BaseAdapter):
    entity = "work_centers"
    odoo_model = "mrp.workcenter"
    ingest_table = "cdm_ingest_work_center"
    odoo_fields = ["id", "name", "code", "time_efficiency", "capacity"]

    def transform_to_canonical(self, odoo_record: dict) -> CanonicalRecord | None:
        oid = str(odoo_record.get("id"))
        key = odoo_record.get("code") or f"WC-{oid}"
        eff = odoo_record.get("time_efficiency")
        return CanonicalRecord(
            table=self.ingest_table,
            natural_key=key,
            fields={
                "name": odoo_record.get("name") or key,
                "capacity_hours": odoo_record.get("capacity"),
            },
            source_id=oid,
            payload={
                **{k: v for k, v in odoo_record.items() if v not in (None, False)},
                "efficiency_factor": (float(eff) / 100.0) if eff not in (None, False) else None,
                "source_system": "odoo",
                "source_id": oid,
                "synced_at": datetime.now(UTC).isoformat(),
            },
        )


class CalendarAdapter(BaseAdapter):
    entity = "calendars"
    odoo_model = "resource.calendar"
    ingest_table = "cdm_ingest_capacity_calendar"
    odoo_fields = ["id", "name"]

    def transform_to_canonical(self, odoo_record: dict) -> CanonicalRecord | None:
        oid = str(odoo_record.get("id"))
        key = f"CAL-{oid}"
        return CanonicalRecord(
            table=self.ingest_table,
            natural_key=key,
            fields={"work_center_id": None},
            source_id=oid,
            payload={
                "name": odoo_record.get("name"),
                "source_system": "odoo",
                "source_id": oid,
                "synced_at": datetime.now(UTC).isoformat(),
            },
        )


class ProductAdapter(BaseAdapter):
    entity = "products"
    odoo_model = "product.template"
    ingest_table = "cdm_ingest_product"
    odoo_fields = ["id", "name", "default_code", "type", "uom_id", "categ_id"]
    domain = [["type", "in", ["product", "consu"]]]

    def transform_to_canonical(self, odoo_record: dict) -> CanonicalRecord | None:
        ptype = odoo_record.get("type")
        # Finished goods vs raw: consu/raw stay materials adapter
        if ptype in ("consu",):
            return None
        oid = str(odoo_record.get("id"))
        key = odoo_record.get("default_code") or f"PT-{oid}"
        return CanonicalRecord(
            table=self.ingest_table,
            natural_key=key,
            fields={
                "name": odoo_record.get("name") or key,
                "product_type": ptype,
                "uom": _m2o_name(odoo_record.get("uom_id")),
            },
            source_id=oid,
            payload={
                **{k: v for k, v in odoo_record.items() if v not in (None, False)},
                "source_system": "odoo",
                "source_id": oid,
                "synced_at": datetime.now(UTC).isoformat(),
            },
        )


class MaterialAdapter(BaseAdapter):
    entity = "materials"
    odoo_model = "product.template"
    ingest_table = "cdm_ingest_material"
    odoo_fields = ["id", "name", "default_code", "type", "categ_id", "uom_id"]
    domain = [["type", "=", "consu"]]

    def transform_to_canonical(self, odoo_record: dict) -> CanonicalRecord | None:
        oid = str(odoo_record.get("id"))
        key = odoo_record.get("default_code") or f"MAT-{oid}"
        return CanonicalRecord(
            table=self.ingest_table,
            natural_key=key,
            fields={"name": odoo_record.get("name") or key},
            source_id=oid,
            payload={
                **{k: v for k, v in odoo_record.items() if v not in (None, False)},
                "source_system": "odoo",
                "source_id": oid,
                "synced_at": datetime.now(UTC).isoformat(),
            },
        )


class BomAdapter(BaseAdapter):
    entity = "boms"
    odoo_model = "mrp.bom"
    ingest_table = "cdm_ingest_bom"
    odoo_fields = ["id", "product_tmpl_id", "product_id", "product_qty", "code"]

    def transform_to_canonical(self, odoo_record: dict) -> CanonicalRecord | None:
        oid = str(odoo_record.get("id"))
        key = odoo_record.get("code") or f"BOM-{oid}"
        return CanonicalRecord(
            table=self.ingest_table,
            natural_key=key,
            fields={"product_id": _m2o_id(odoo_record.get("product_tmpl_id") or odoo_record.get("product_id"))},
            source_id=oid,
            payload={
                **{k: v for k, v in odoo_record.items() if v not in (None, False)},
                "output_qty": odoo_record.get("product_qty"),
                "source_system": "odoo",
                "source_id": oid,
                "synced_at": datetime.now(UTC).isoformat(),
            },
        )


class RoutingAdapter(BaseAdapter):
    entity = "routings"
    odoo_model = "mrp.routing.workcenter"
    ingest_table = "cdm_ingest_routing"
    odoo_fields = ["id", "name", "workcenter_id", "bom_id", "time_cycle"]

    def transform_to_canonical(self, odoo_record: dict) -> CanonicalRecord | None:
        oid = str(odoo_record.get("id"))
        key = f"RTG-{oid}"
        return CanonicalRecord(
            table=self.ingest_table,
            natural_key=key,
            fields={"product_id": _m2o_id(odoo_record.get("bom_id"))},
            source_id=oid,
            payload={
                **{k: v for k, v in odoo_record.items() if v not in (None, False)},
                "source_system": "odoo",
                "source_id": oid,
                "synced_at": datetime.now(UTC).isoformat(),
            },
        )


class SupplierAdapter(BaseAdapter):
    entity = "suppliers"
    odoo_model = "res.partner"
    ingest_table = "cdm_ingest_supplier"
    odoo_fields = ["id", "name", "supplier_rank", "customer_rank", "email", "phone"]
    domain = [["supplier_rank", ">", 0]]

    def transform_to_canonical(self, odoo_record: dict) -> CanonicalRecord | None:
        if int(odoo_record.get("supplier_rank") or 0) <= 0:
            return None
        oid = str(odoo_record.get("id"))
        key = f"SUP-{oid}"
        return CanonicalRecord(
            table=self.ingest_table,
            natural_key=key,
            fields={"name": odoo_record.get("name") or key},
            source_id=oid,
            payload={
                **{k: v for k, v in odoo_record.items() if v not in (None, False)},
                "source_system": "odoo",
                "source_id": oid,
                "synced_at": datetime.now(UTC).isoformat(),
            },
        )


class CustomerAdapter(BaseAdapter):
    entity = "customers"
    odoo_model = "res.partner"
    ingest_table = "cdm_ingest_customer"
    odoo_fields = ["id", "name", "supplier_rank", "customer_rank", "email"]
    domain = [["customer_rank", ">", 0]]

    def transform_to_canonical(self, odoo_record: dict) -> CanonicalRecord | None:
        if int(odoo_record.get("customer_rank") or 0) <= 0:
            return None
        oid = str(odoo_record.get("id"))
        key = f"CUST-{oid}"
        return CanonicalRecord(
            table=self.ingest_table,
            natural_key=key,
            fields={"name": odoo_record.get("name") or key},
            source_id=oid,
            payload={
                **{k: v for k, v in odoo_record.items() if v not in (None, False)},
                "source_system": "odoo",
                "source_id": oid,
                "synced_at": datetime.now(UTC).isoformat(),
            },
        )


class EmployeeAdapter(BaseAdapter):
    entity = "employees"
    odoo_model = "hr.employee"
    ingest_table = "cdm_ingest_employee"
    odoo_fields = ["id", "name", "barcode", "department_id", "job_id"]

    def transform_to_canonical(self, odoo_record: dict) -> CanonicalRecord | None:
        oid = str(odoo_record.get("id"))
        key = odoo_record.get("barcode") or f"EMP-{oid}"
        return CanonicalRecord(
            table=self.ingest_table,
            natural_key=key,
            fields={
                "employee_name": odoo_record.get("name") or key,
                "department": _m2o_name(odoo_record.get("department_id")),
                "role": _m2o_name(odoo_record.get("job_id")),
            },
            source_id=oid,
            payload={
                **{k: v for k, v in odoo_record.items() if v not in (None, False)},
                "source_system": "odoo",
                "source_id": oid,
                "synced_at": datetime.now(UTC).isoformat(),
            },
        )


ADAPTER_ORDER: list[type[BaseAdapter]] = [
    PlantAdapter,
    CalendarAdapter,
    WorkCenterAdapter,
    ProductAdapter,
    MaterialAdapter,
    BomAdapter,
    RoutingAdapter,
    SupplierAdapter,
    CustomerAdapter,
    EmployeeAdapter,
]
