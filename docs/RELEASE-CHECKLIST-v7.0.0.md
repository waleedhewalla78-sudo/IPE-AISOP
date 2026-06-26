# IPE v7.0.0 Release Checklist

**Date:** 2026-06-26  
**Release commit:** `ccbedfe`  
**Tag:** `v7.0.0`

---

## Automated Results

| Check | Target | Actual | Status |
|-------|--------|--------|--------|
| Demo scenarios | 20/20 | **20/20** | ✅ `docs/final-regression-demo.txt` |
| Chaos tests | 6/6 | **6/6** | ✅ `docs/final-regression-chaos.txt` |
| Speckit built | 162/162 | **162/162** | ✅ |
| Speckit readiness | 100/100 | **100/100** | ✅ |
| Audit score | 100/100 | **100/100** | ✅ `docs/audit-final-score-v7.md` |
| Test coverage | ≥75%/svc | **~78% avg** | ✅ `docs/coverage-report-v7.md` |
| FR-P verified | 14/14 or ADR | **13/14 + ADR-001** | ✅ |

### Coverage by service (P8 final)

| Service | Coverage | Gate |
|---------|----------|------|
| nlp-svc | 77.94% | 75% ✅ |
| fea-svc | 75.25% | 75% ✅ |
| cap-svc | 75.48% | 75% ✅ |
| mat-svc | 75.77% | 75% ✅ |
| dpe-svc | 75.77% | 75% ✅ |
| alert-svc | 88.54% | 75% ✅ |

> auth-svc and mdr-svc live inside dpe-svc.

---

## Security

| Check | Result |
|-------|--------|
| Hardcoded secrets | CLEAN |
| Non-root containers | PARTIAL (POST-C4 backlog) |
| CORS restricted | YES (prod path) |
| Health endpoints | `/health` + `/healthz` |
| Tenant isolation | VERIFIED + ADR-002 waiver |
| SQL injection safe | YES |
| Input validation | PYDANTIC |

---

## Documentation

| Document | Status |
|----------|--------|
| README.md | ✅ |
| CHANGELOG.md | ✅ |
| CONTRIBUTING.md | ✅ |
| docs/architecture.md | ✅ |
| docs/api-reference.md | ✅ |
| docs/deployment.md | ✅ |
| docs/runbooks/* | ✅ |
| .env.example | ✅ |

---

## Git Tags

v1.0.0, v6.0.0, v6.0.1, v6.1.0, **v7.0.0** ✅

---

## Sign-off

- [x] Speckit 162/162
- [x] Audit 100/100 documented
- [x] Documentation suite complete
- [x] Security sweep documented
- [x] Coverage ≥75% per service
- [x] Live demo 20/20 (P11)
- [x] Chaos 6/6 (P11)
- [x] v7.0.0 tag
- [ ] Remote push (P12) — **only remaining gate**

---

## P12 — Remote Push

```powershell
git -c safe.directory=E:/AISOP/ipe remote add origin <YOUR_REPO_URL>
git -c safe.directory=E:/AISOP/ipe push -u origin master --tags
```
