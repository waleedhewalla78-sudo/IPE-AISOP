# OPEN Items — Program (honest tracker)

**Updated:** 2026-07-18  
**Do not auto-close COM items.**

## Commercial / Human (OPEN)

| ID | Item | Owner | Blocks |
|----|------|-------|--------|
| OQ-7 | Licence / implementation price | Waleed | SOW send |
| OQ-1 | Odoo 17 vs 19 confirm | Star Trans IT | Staging clarity |
| PH1-01 | SOW send | COM | Depends OQ-7 |
| PH1-02 | Live Odoo staging | Ops / Customer IT | Live sync UAT + live write-back |
| G-R2-04 | Arabic native QA sign-off | Native reviewer | `v9.1.1-r2` tag |
| OQ-9 | Gate 11 waiver signatures | Waleed | Formal waiver |

## Engineering residuals (OPEN)

| Item | Notes |
|------|-------|
| Spec 022 #70/#72/#110 Docker validate | Re-run when R2 stack fully healthy |
| Phase 8B multi-site A18 live + Odoo write-back expansion | Deferred (stubs in 8A) |
| Phase 8C full Arabic + Excel everywhere + SOC 2 prep | Deferred |
| Phase 8D partner programme + launch | Deferred |
| Live Kong smoke `/api/v1/phase8/*` | After image rebuild + healthy gateway |
| Spec 025 Digital Factory polish | Shop-floor linked only |
| Spec 026 collaborative planning / WhatsApp / alert inbox | Deferred beyond Wave 1 |
| Spec 028 Digital Gemba live IoT / operator tablet / Andon push | STUB / Wave 2 |
| Spec 028 monetary net-saving in leveling | Deferred |
| Under-load k6 p95 | Spec 029 notes — residual risk |

## Engineering CLOSED this run (Phase 8 / 029)

| Item | Notes |
|------|-------|
| Spec 029 Kong enterprise / Andon dual-write / RLS 068 / MPS-MRP 069 / stage-gate | ENG COMPLETE Wave 1 |
| Spec 030 Ollama degrade + roles + write-back 070 + Excel types + A18–A20 stubs | ENG COMPLETE Wave 1 (8A) |
| INT-01 Kong `/enterprise` route object | Shipped in Spec 029 (live smoke stack-dependent) |

## Tags

| Tag | Status |
|-----|--------|
| v9.1.1-r2 | HOLD until G-R2-04 |
| v9.1.0-r2 | **Do not push** (stale) |
| v9.3.0-r1-eng | Not applied (COM CONDITIONAL) |

## Completed (eng)

| Item | Spec |
|------|------|
| Ops Phase 3 Wave 1 cores | 024 |
| Phase 4 Premium Wave 1 | 025 |
| Phase 5 Planning-Command Wave 1 | 026 |
| Phase 6 Enterprise Agentic Wave 1 | 027 |
| Phase 7 Deep Planning Wave 1 | 028 |
| Productionization Wave 1 | 029 |
| Phase 8 Wave 1 (8A) R1 production scaffold | 030 |
