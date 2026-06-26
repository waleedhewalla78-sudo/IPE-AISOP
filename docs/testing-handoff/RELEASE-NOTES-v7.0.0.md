## IPE v7.0.0 — Production-Ready Enterprise Release

### What's Included

- 14+ microservices (dpe, cap, mat, fea, res, del, nlp, alert, connector, scn, network, rec, + React web)
- Kong API Gateway with JWT authentication (auth + MDR in **dpe-svc**)
- PostgreSQL CDM with Row-Level Security
- Kafka event mesh for async messaging
- Prometheus + Loki + Grafana monitoring stack (when ops overlay enabled)
- **20/20** demo scenarios verified
- **6/6** chaos engineering tests passing
- **75%+** test coverage across all core services
- **100/100** audit score (documented)
- **162/162** Speckit requirements built

### Quick Start

See [docs/testing-handoff/QUICK-START.md](docs/testing-handoff/QUICK-START.md)

### Documentation

- [Architecture](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Deployment Guide](docs/deployment.md)
- [Runbooks](docs/runbooks/)
- [Changelog](CHANGELOG.md)
- [Full demo guide](docs/FULL-DEMO-GUIDE.md)

### Known Limitations

- Keycloak IdP integration deferred to **v8.0.0** ([ADR-001](docs/decisions/ADR-001-keycloak-deferral.md))
- Legacy RLS policies 002–012 waived ([ADR-002](docs/decisions/ADR-002-legacy-rls-waiver.md))
- Web UI (:8082) runs via `npm run dev` in `apps/web` — not part of Docker demo overlay

### Post-v7 Backlog

- **v8.0.0:** Keycloak integration (FR-P-13)
- **POST-C3:** RLS policy modernization
- **POST-C4:** Non-root container hardening
- **POST-A/B/D:** Scale, ERP connectors, commercial features

See [docs/IPE-v6-MASTER-EXECUTION-PLAN.md](docs/IPE-v6-MASTER-EXECUTION-PLAN.md)
