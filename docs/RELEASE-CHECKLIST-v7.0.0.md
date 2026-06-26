# IPE v7.0.0 Release Checklist

**Date:** 2026-06-26 (updated)  
**Latest commit:** pending P6-05 / P7 / P8 continuation

---

## Automated Results

| Check | Target | Actual | Status |
|-------|--------|--------|--------|
| Demo scenarios | 20/20 | 20/20 (v6.1.0 evidence) | ⚠️ Re-run P11 |
| Chaos tests | 6/6 | 6/6 (v6.1.0 evidence) | ⚠️ Re-run P11 |
| Speckit built | 162/162 | **162/162** | ✅ |
| Speckit readiness | 100/100 | **100/100** | ✅ |
| Audit score | 100/100 | **100/100** | ✅ |
| Test coverage | ≥75%/svc | **~64% avg** | ❌ Blocker |
| FR-P verified | 14/14 or ADR | **13/14 + ADR-001** | ✅ |

---

## Security

| Check | Result |
|-------|--------|
| Hardcoded secrets | CLEAN |
| Non-root containers | PARTIAL (POST-C4) |
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

## Git Tags (current)

v1.0.0, v6.0.0, v6.0.1, v6.1.0 — **v7.0.0 NOT tagged** (coverage + regression pending)

---

## Sign-off

- [x] Speckit 162/162
- [x] Audit 100/100 documented
- [x] Documentation suite complete
- [x] Security sweep documented
- [ ] Coverage ≥75% per service
- [ ] Live demo 20/20 re-run
- [ ] Chaos 6/6 re-run
- [ ] v7.0.0 tag
- [ ] Remote push (P12)
