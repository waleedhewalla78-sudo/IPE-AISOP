# Changelog

All notable changes to the IPE platform are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [v7.0.0] — 2026-06-26 (in progress)

### Added

- Phase 5 gap analysis reports (speckit, audit, coverage, documentation)
- Speckit 162/162 completion (T049–T051 closed; T053 cancelled)
- ADR-001 Keycloak deferral to v8.0.0
- Documentation suite: CHANGELOG, CONTRIBUTING, runbooks, architecture index, API reference
- Security hardening sweep documentation

### Changed

- Coverage gate target raised toward 75% per service
- READINESS.md updated for v7.0.0 completion track

---

## [v6.1.0] — 2026-06-26

### Added

- TLS internal services runbook (`docs/runbooks/tls-internal.md`)
- JWT rotation runbook (`docs/runbooks/jwt-rotation.md`)
- Migration 028: SEC-05 password_hash backfill
- Wave 3 live regression evidence (demo 20/20, chaos 6/6)

### Fixed

- Auth password verification for `{SHA-256}` hashed credentials
- MDR fail-closed gate (503) on capacity endpoints
- Optimistic locking on schedule approve (409 conflict)

---

## [v6.0.1] — 2026-06-25

### Fixed

- MDR internal JWT forwarding for cross-service calls
- Audit fixes C-01, BUG-02, BUG-03 live-verified

---

## [v6.0.0] — 2026-06-24

### Added

- V6 features: tariff shock, visual CPM, predictive maintenance, cost of chaos, war room
- Demo 20/20 live gate
- Speckit 004 AI-first V6 complete (55/55 tasks)

---

## [v1.0.0] — 2026-06-22

### Added

- Initial production release
- 14-service microservices architecture
- Kong API gateway with JWT auth
- Demo stack and critical path E2E (Gate 2 passed)
- PostgreSQL CDM with tenant RLS (migrations 024+)
