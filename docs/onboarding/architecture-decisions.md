# Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Microservices with CDM | Independent scaling, single source of truth |
| API Framework | FastAPI | Async, auto OpenAPI, Pydantic |
| Database | PostgreSQL 16 + TimescaleDB | Relational + time-series |
| Event Mesh | Apache Kafka | Decoupled, durable event pipeline |
| Constraint Solver | Google OR-Tools | Open-source CP-SAT |
| Frontend | React 18 + TypeScript + Tailwind | Modern SPA with type safety |
| Deployment | Kubernetes + ArgoCD | GitOps, scalability |
| CI/CD | GitHub Actions | Integrated with GitHub |
