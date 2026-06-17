# SAP Adapter — IPE Enterprise Connector

Integrates SAP S/4HANA and ECC with the IPE platform via the IPE Canonical Data Model (CDM).

## Required OData / BAPI Endpoints

| SAP Object | BAPI / OData | Purpose |
|-----------|-------------|---------|
| Sales Order Header | `BAPI_SALESORDER_GETDETAIL` / `API_SALES_ORDER_SRV` | Read VBAK fields |
| Sales Order Item | `BAPI_SALESORDER_GETDETAIL` (item tables) / `API_SALES_ORDER_SRV` | Read VBAP fields |
| Production Operation | `BAPI_PRODORD_GET_DETAIL` / `API_MANUFACTURING_ORDER_SRV` | Read AFVC / AFVV fields |
| Work Center | `BAPI_WORK_CENTER_GETDETAIL` / `API_WORK_CENTER_SRV` | Read work center capacity |

## Authentication

- **mTLS** (client certificate) for production S/4HANA connections.
- **Basic Auth** over HTTPS for sandbox / dev systems.
- Credentials stored in `ipe.config` (Odoo) — field `erp_base_url`, `api_secret`.

## Mapping File

`cdm_mapper.py` provides two functions:

- `map_vbak_vbap_to_demand_line(row, tenant_id)` → `cdm_demand_line`
- `map_afvc_afvv_to_work_order(row, tenant_id, mo_erp_id)` → `cdm_work_order`

## Scheduled Sync

The Odoo connector's `process_queue` cron pushes SAP data as IPE events.
A dedicated SAP OData poller runs as a separate service (see `services/connector/`).

## Rate Limits

- Max 100 BAPI calls/minute per tenant (configurable via `ipe.config`).
- 30-second timeout on all OData calls.
