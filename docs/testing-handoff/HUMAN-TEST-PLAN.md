# IPE v7.0.0 — Human Acceptance Test Plan

**Version:** v7.0.0  
**Repository:** https://github.com/waleedhewalla78-sudo/IPE-AISOP  
**Estimated time:** 4–6 hours (full pass)

---

## Prerequisites

- Docker Desktop running
- Node.js 18+ (for web UI on :8082)
- Stack started: `.\scripts\rel-demo-stack.ps1 -SkipBuild`
- Web UI: `cd apps\web && npm run dev` → http://localhost:8082
- Kong API: http://localhost:8000
- Guide reference: [FULL-DEMO-GUIDE.md](../FULL-DEMO-GUIDE.md)

---

## Test Accounts

| Role | Email | Password | Tenant ID |
|------|-------|----------|-----------|
| Admin (demo) | `Ahmed@nour` | `admin` | `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11` |
| Admin (alt) | `admin@demo.com` | `demo` | same |

Use header `X-Tenant-ID: a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11` on all API calls.

---

## Test Scenarios (20)

Record **PASS / FAIL / N/A** and notes for each.

### Category 1: Production Planning (1–5)

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 1 | Feasibility queue | Login → Control Tower | 10 MOs listed; scores visible |
| 2 | Material ATP check | Copilot: "Widget A stock" OR API `POST /api/v1/material/check-availability` | Availability response with qty |
| 3 | Demand / priority | Executive or API demand classify | No 500; priority data returned |
| 4 | Schedule optimization | Schedule page → run schedule for demo MOs | Gantt/operations returned; status 200 |
| 5 | Tariff shock | Tariff page OR demo CP 18 path | Affected MOs + substitute drafts |

### Category 2: Material Management (6–10)

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 6 | BOM / material status | Copilot material query for Widget A / Gadget B | Component quantities in response |
| 7 | Supplier scorecards | SCN Portal | Scorecards for seeded suppliers |
| 8 | Material shortage alert | War Room / alerts feed | Active alerts for demo MOs |
| 9 | Demand-supply matching | Resolution Center scenarios | Scenarios loaded for demo MOs |
| 10 | Inventory summary | Copilot inventory query | 4 finished goods with on-hand qty |

### Category 3: NLP / AI (11–13)

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 11 | Copilot plan query | Copilot: "Which orders are at risk?" | Structured intent + feasibility summary |
| 12 | LLM fallback | With demo overlay (no external LLM), ask copilot question | 200 response; rule-based fallback text |
| 13 | War room recovery | War Room page | Recovery options ranked (top 3) |

### Category 4: Operational (14–17)

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 14 | JWT auth | Login via UI; API call with/without token | 401 without token; 200 with valid JWT |
| 15 | Schedule approve persist | Schedule → approve 2 demo MOs (CP 15) | Persisted count ≥ 1; no 500 |
| 16 | MDR gate | Attempt schedule when MDR unavailable (optional: stop dpe-svc briefly) | Fail-closed / 503 — not silent pass |
| 17 | Service resilience | Stop `nlp-svc`; call feasibility + schedule APIs | Non-NLP paths still 200 (chaos C1) |

### Category 5: Monitoring & V6 Features (18–20)

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 18 | V6-R1 margin priority | Schedule page margin-aware ordering (CP 17) | Margin scores visible |
| 19 | V6-R3 CPM cascade | Schedule cascade action (CP 19) | Completes in <2s |
| 20 | V6-R4/R5 maintenance + chaos | IoT telemetry + War Room chaos categories (CP 20) | Maintenance block + chaos categories |

---

## Pass Criteria

- All 20 scenarios **PASS** or documented **N/A** with justification
- No unexplained **500** errors in service logs during testing
- Tenant header required on mutating API calls
- Automated baseline already green: 20/20 demo + 6/6 chaos (see [EVIDENCE-INDEX.md](EVIDENCE-INDEX.md))

---

## Defect Reporting

**GitHub Issues:** https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues

| Field | Content |
|-------|---------|
| Title | `[UAT] <short summary>` |
| Steps | Numbered reproduction steps |
| Expected | What should happen |
| Actual | What happened |
| Severity | P1 (blocker) / P2 (major) / P3 (minor) |
| Environment | OS, Docker version, commit/tag (`v7.0.0`) |
| Logs | `docker logs <container> --tail 50` |

---

## Sign-off

| Role | Name | Date | Result |
|------|------|------|--------|
| Tester | | | /20 pass |
| Product owner | | | Approved / Rejected |
