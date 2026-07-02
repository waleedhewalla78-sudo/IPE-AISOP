# Clarify — 008 v8 Phase 2

| Topic | Decision |
|-------|----------|
| equipment-svc port | **8061** — port 8080 used by Kafka UI/Airflow |
| Supply vs mat-svc | supply-svc orchestrates; mat-svc keeps ATP/CTP math |
| Orders vs demand lines | New `cdm_customer_order*` tables; separate from `cdm_demand_line` |
| IoT ingest | equipment-svc writes telemetry; cap-svc `/iot/telemetry` unchanged |
| Default Supply Chain tab | Supply Planning (was Tariff) |
