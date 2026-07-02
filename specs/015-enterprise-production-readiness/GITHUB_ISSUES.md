# GitHub Issues — 015 Enterprise Production Readiness

**Generated**: 2026-06-24 via `/speckit.taskstoissues`  
**Milestone**: `v10.0.0-enterprise`  
**Labels**: `enterprise`, `015`, `P0`

---

## Epic: IPE Enterprise Program (36 weeks)

**Title**: `EPIC-015: Demo → Enterprise Production (Phases 0–4)`

**Body**: Synthesizes Enterprise Deployment Roadmap, v8.2.0 gap closure (complete), SAP gap analysis, and POST-B scaffolds. Depends on 014 R2 completion.

---

## Phase 0 issues

| Issue | Title | Tasks |
|-------|-------|-------|
| ENT-001 | Keycloak OIDC activation | T001, T007 |
| ENT-002 | Vault + AWS Secrets Manager providers | T003, T004, T009 |
| ENT-003 | RS256 JWT + Kong TLS | T002, T005 |
| ENT-004 | API audit request middleware | T006 |

## Phase 1 issues

| Issue | Title | Tasks |
|-------|-------|-------|
| ENT-010 | Helm full service deployment | T030–T032 |
| ENT-011 | Data layer HA (PG, Kafka, Redis) | T033–T036 |
| ENT-012 | Graceful shutdown + circuit breakers | T037, T038 |

## Phase 2–4 issues

See `tasks.md` T060–T128 — create per sprint during phase kickoff.

---

```powershell
# Example: gh issue create (after gh auth login)
cd E:\AISOP\ipe
gh issue create --title "ENT-001: Keycloak OIDC activation" --label "enterprise,P0" --body-file specs/015-enterprise-production-readiness/issues/ENT-001.md
```

---

*Issues template v1.0 — `/speckit.taskstoissues`*
