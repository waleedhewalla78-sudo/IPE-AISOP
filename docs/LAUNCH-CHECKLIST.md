# IPE Launch Checklist

**Target**: Client demo + staging launch @ **v1.0.0 + V6-R1**  
**Readiness**: 93/100 → production promotion after optional R4 live evidence  
**Last verified**: run `.\scripts\launch-verify.ps1`

---

## 1. Pre-flight (once per environment)

| Step | Command / action | Pass criteria |
|------|------------------|---------------|
| Docker stack | `docker compose -f infrastructure/docker/docker-compose.yml up -d` | All services healthy |
| Migrations | `make migrate` | No errors; migration 024 applied |
| Seed data | `.\scripts\seed-demo-client.ps1` | Demo tenant MOs + activity cost drivers |
| Kong routes | `docker compose -f infrastructure/docker/docker-compose.yml up -d --force-recreate kong` | API @ `:8000` responds |

---

## 2. Automated verification

| Step | Command | Pass criteria |
|------|---------|---------------|
| **Full backend tests** | `.\scripts\launch-verify.ps1` | All service suites green |
| **Demo walkthrough** | `.\scripts\run-full-demo.ps1` | 17/17 checkpoints pass |
| **Frontend unit** | `cd apps/web; pnpm test -- --run` | Vitest green |
| **E2E (optional)** | `cd apps/web; pnpm test:e2e` | Playwright green (stack running) |

---

## 3. Functional smoke (manual)

| Module | URL | Verify |
|--------|-----|--------|
| Login | http://localhost:8082/login | `Ahmed@nour` / `admin` |
| Control Tower | `/control-tower` | Feasibility queue, KPIs |
| Schedule | `/schedule` | Gantt + approve flow |
| Copilot | `/copilot` | NL query returns data |
| War Room | `/war-room` | Alerts feed |
| V6-R1 margin | API `GET /api/v1/demand/priority/margin-aware` | Priorities + warnings |
| V6-R1 schedule | API `POST /api/v1/capacity/schedule` `{ "strategy": "activity_optimized" }` | `activity_cost_breakdown` present |
| Guardrail | Approve MO with `feasibility_score < 85` | Blocked; audit event |

---

## 4. Security & tenancy

- [ ] JWT required on all `/api/v1/*` routes (except auth/login)
- [ ] `X-Tenant-ID` enforced; cross-tenant reads return empty/403
- [ ] RLS active on tenant-scoped tables (`cdm_*`)
- [ ] Audit log append-only (no UPDATE/DELETE)

---

## 5. Known blockers (non-launch for enterprise SSO)

| Item | Impact | Workaround |
|------|--------|------------|
| Keycloak live IdP (C-007) | No SAML/SCIM | Demo JWT auth |
| SAP/D365 live sandbox | No live ERP sync | Mock Odoo + mapper tests |
| k6 200 VU / Chaos Mesh evidence | R4 score cap | Scripts ready; run before prod claim |
| V6-R2–R5 (40 tasks) | Tariff, CPM, predictive, chaos UI | Not required for v1.0.0 demo launch |

---

## 6. Release artifacts

| Artifact | Location |
|----------|----------|
| Readiness score | `READINESS.md` |
| Program status | `specs/005-ipe-program-status/spec.md` |
| Release notes | `RELEASE_NOTES.md` |
| Demo guide | `docs/FULL-DEMO-GUIDE.md` |
| Notion tracker | [IPE Task Tracker v2](https://app.notion.com/p/788f0c170abe4648b482587d41745625) |

---

## 7. Go / no-go

**GO** when:

1. `launch-verify.ps1` exits 0  
2. `run-full-demo.ps1` exits 0  
3. Stakeholder sign-off on READINESS.md residual risks  

**Tag** (when approved): `v1.0.0` (current) or `v6.0.0` after V6-R5 complete.
