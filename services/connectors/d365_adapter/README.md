# D365 Adapter — IPE Enterprise Connector

Integrates Microsoft Dynamics 365 (Sales, Supply Chain Management) with the IPE platform via the IPE Canonical Data Model (CDM).

## Required Dataverse / OData Endpoints

| D365 Entity | OData Endpoint | Purpose |
|------------|---------------|---------|
| Sales Order | `salesorders` | Read order header (VBAK equivalent) |
| Sales Order Detail | `salesorderdetails` | Read order line items (VBAP equivalent) |
| Work Order | `msdyn_workorders` | Read production work orders (AFVC equivalent) |
| Product | `products` | Read product master data |
| Account | `accounts` | Read customer data |

Base URL pattern: `https://{org}.crm.dynamics.com/api/data/v9.2/`

## Authentication

- **OAuth 2.0** (Azure AD) using client credentials flow.
- Required scopes: `https://{org}.crm.dynamics.com/.default`
- Tenant ID, Client ID, and Client Secret stored in `ipe.config` (Odoo).
- Token refresh handled automatically via `msal` (Microsoft Authentication Library).

## Mapping File

`cdm_mapper.py` provides two functions:

- `map_sales_order_to_demand_line(row, tenant_id)` → `cdm_demand_line`
- `map_work_order_to_cdm(row, tenant_id, mo_erp_id)` → `cdm_work_order`

## Scheduled Sync

A lightweight background worker (see `services/connector/`) polls the Dataverse
`_modifiedon` filter every 15 minutes and posts changes as IPE Kafka events.

## Rate Limits

- Dataverse API: 60,000 requests/hour per environment (scalable).
- IPE connector respects `Retry-After` headers and uses exponential backoff.
