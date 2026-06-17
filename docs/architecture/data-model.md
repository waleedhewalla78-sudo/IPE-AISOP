# Data Model

The Canonical Data Model (CDM) normalizes ERP-specific schemas into a unified format.

## Core Tables

| Table | Purpose |
|-------|---------|
| `cdm_tenant` | Multi-tenant configuration |
| `cdm_product` | Product master data |
| `cdm_bill_of_material` | BOM header with versioning |
| `cdm_bom_line` | Component requirements |
| `cdm_demand_line` | Customer demand with priority scores |
| `cdm_supply_order` | Purchase orders and scheduled receipts |
| `cdm_manufacturing_order` | Production orders with feasibility scores |
| `cdm_work_order` | Individual routing operations |
| `cdm_work_center` | Capacity resources |
| `cdm_operator` | Labor resources |
| `cdm_inventory_position` | Time-series inventory (TimescaleDB hypertable) |
| `cdm_delay_event` | Delay root cause records |
| `cdm_resolution_scenario` | Resolution proposals |

## Key Design Decisions

- All tenant-scoped tables have RLS enforced
- Inventory uses TimescaleDB for time-series queries
- Audit log is append-only (no UPDATE/DELETE)
- UUID primary keys throughout
