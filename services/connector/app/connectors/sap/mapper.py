"""SAP S/4HANA → CDM field mapper (scaffold)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SAPConnectionConfig:
    sap_url: str
    sap_client_id: str
    sap_client_secret: str
    sap_system: str
    sap_tenant_id: str
    sap_api_version: str = "v2"
    verify_ssl: bool = True


PRODUCT_MAPPING = {
    "Product": "internal_ref",
    "ProductDescription": "name",
    "ProductType": "source_type",
    "BaseUnit": "unit_of_measure",
    "ProductGroup": "product_group",
    "MaterialGroup": "material_group",
}

MO_MAPPING = {
    "ManufacturingOrder": "erp_mo_id",
    "MOProduct": "product_id",
    "MOQuantity": "quantity",
    "MOStartDate": "planned_start",
    "MOEndDate": "planned_end",
    "MOStatus": "status",
    "MOProductionPlant": "plant_id",
}

_STATUS_MAP = {
    "CRTD": "draft",
    "REL": "released",
    "PRC": "in_progress",
    "TECO": "completed",
    "CLSD": "closed",
}


def map_sap_product(sap_product: dict) -> dict:
    cdm: dict = {"source_type": "sap"}
    for sap_field, cdm_field in PRODUCT_MAPPING.items():
        if sap_field in sap_product:
            cdm[cdm_field] = sap_product[sap_field]
    return cdm


def map_sap_mo(sap_mo: dict) -> dict:
    cdm: dict = {"source_type": "sap"}
    for sap_field, cdm_field in MO_MAPPING.items():
        if sap_field in sap_mo:
            cdm[cdm_field] = sap_mo[sap_field]
    sap_status = sap_mo.get("MOStatus", "")
    cdm["status"] = _STATUS_MAP.get(sap_status, str(sap_status).lower())
    return cdm
