# System Overview

## Layers

1. **ERP Connectors** — Thin adapters that normalize ERP data into the CDM
2. **Event Mesh (Kafka)** — Decoupled communication between all services
3. **AI Services** — 7 microservices for demand, material, capacity, feasibility, resolution, delay, and NLP
4. **API Gateway (Kong)** — JWT auth, rate limiting, tenant routing
5. **Frontend (React SPA)** — Control Tower, Resolution Center, Copilot, Shop Floor, Admin
6. **CDM Database (PostgreSQL/TimescaleDB)** — Single source of truth with RLS

## Data Flow

```
ERP → Connector → CDM → Kafka → AI Services → CDM → Connector → ERP
```

## Autonomy Progression

- Shadow Mode — Observe only, no action
- Suggest Mode — Recommend but require approval
- Autonomous Mode — Act within defined boundaries
