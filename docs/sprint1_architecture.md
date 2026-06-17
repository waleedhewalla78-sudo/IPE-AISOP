# Sprint 1 Architecture

## 3-Hop Data Flow

```
[Odoo ERP] --(HMAC-signed Webhook)--> [ipe-connector API] --(Publish via confluent-kafka)--> [Kafka: ipe.demand.created]
                                                                                                      |
                                                                                                      v
                     [FastAPI dpe-svc] <--(Consume)--> [Kafka] --> [Redis: Idempotency/DLQ]
                           |
                           +--(Query)--> [PostgreSQL 16 CDM] (Enforced: Safe RLS by tenant_id)
                           |
                           +--(Check)--> [MDR Engine] --> (If < 80%: Block & Return Remediation; persist to cdm_mdr_score)
                           |
                           +--(Response)--> [React Control Tower] (via Nginx reverse proxy + JWT)
```

## Infrastructure Stack (docker-compose.yml)

| Service | Image | Port |
|---------|-------|------|
| Postgres | postgres:16-alpine | 5432 |
| Redis | redis:7-alpine | 6379 |
| Zookeeper | confluentinc/cp-zookeeper:7.7.0 | 2181 |
| Kafka | confluentinc/cp-kafka:7.7.0 | 9092 |
| Schema Registry | confluentinc/cp-schema-registry:7.7.0 | 8081 |
| Nginx | nginx:alpine | 80 |

## CDM Schema (19 Tables)

### Core Entities
1. cdm_tenant - Multi-tenant root
2. cdm_user - Users with role-based access
3. cdm_product - Products with lead time tracking
4. cdm_supplier - Supplier reliability models

### Manufacturing
5. cdm_bill_of_material - BOM headers
6. cdm_bom_line - BOM component lines
7. cdm_manufacturing_order - MO with optimistic locking
8. cdm_routing_operation - Routing sequences
9. cdm_work_center - Capacity definition
10. cdm_work_order - Work order execution

### Supply Chain
11. cdm_supply_order - Purchase/supply orders
12. cdm_demand_line - Customer demand
13. cdm_inventory_position - Inventory snapshots

### Operations
14. cdm_operator - Labor/skills
15. cdm_delay_event - Cause-categorized delays
16. cdm_resolution_scenario - Resolution proposals

### Governance
17. cdm_mdr_score - MDR evaluation history
18. cdm_export_queue - ERP push retry queue
19. cdm_audit_log - Append-only audit trail

## Security

### Row-Level Security
- All tenant-scoped tables use safe RLS policy:
  ```sql
  USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
  ```
- ipe_audit_writer role has BYPASSRLS for centralized audit logging
- Connection checkout listener resets tenant context to prevent cross-request leakage

### MDR Gates
- `POST /api/v1/demand/classify` checks MDR before processing
- Returns 403 + remediation steps if BOM < 80% or lead time < 60%
