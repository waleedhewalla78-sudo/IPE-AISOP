# Analyze — 008 v8 Phase 2

## Integrations

| Module | Phase 2 touch |
|--------|---------------|
| mat-svc | Inventory data for ATP (read `cdm_inventory_position`) |
| scn-svc | Supplier visibility (future facade from supply-svc) |
| cap-svc | IoT telemetry source; maintenance blocks unchanged |
| alert-svc | War room can surface equipment alerts (future) |
| demand-svc | Demand forecasts inform supply plans (future) |
| Phase 1 scenario-svc | Complementary what-if vs supply plan |

## Migration 030

- `cdm_customer_order`, `cdm_customer_order_line`, `cdm_order_promise`
- `cdm_supply_plan`, `cdm_equipment_asset`

## Competitive gap closure (approx.)

| SAP IBP/Joule | Post Phase 2 |
|---------------|--------------|
| Multi-echelon planning | MVP orchestration |
| Order promise ATP/CTP | MVP |
| Predictive maintenance | Extended dashboard + telemetry query |
