# OPEN Items — Program (honest tracker)

**Updated:** 2026-07-18 (finalize pass)  
**Authoritative:** `docs/project/FINAL-PROGRAM-STATUS.md`  
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
| OQ-3 | UI route-level RBAC decision | COM | Support terms / SOW clarity |
| OQ-8 | Customer 2+ pipeline prospects | COM | Pipeline only |

## Engineering residuals (OPEN)

| Item | Notes |
|------|-------|
| Spec 022/024/029/030 #70/#72/#110/#120/#136 Docker validate | Re-run when R2 stack healthy (Docker down 2026-07-18 finalize) |
| Live Kong smoke `/enterprise/*` + `/phase8/*` | Routes shipped; smoke when gateway up |
| Under-load k6 p95 | Spec 029 notes — residual risk |
| Playwright flakes (Arabic tablet / mobile a11y) | Notes + stub; stabilize |
| RLS residual tables (post-068 audit) | Close remaining if still off |
| Phase 8B–8D | Deferred (stubs in 8A) |
| Spec 026 collaborative / WhatsApp / alert inbox | Wave 2 |
| Spec 028 live IoT / operator tablet / Andon push | STUB / Wave 2 |
| Spec 028 monetary net-saving in leveling | Deferred |

## Engineering CLOSED (do not re-open)

| Item | Notes |
|------|-------|
| Specs 022–030 Wave 1 (030 = 8A) | ENG COMPLETE |
| INT-01 Kong `/api/v1/enterprise` (+ `/phase8`) | Shipped R2 + star-trans |
| Spec 029 Andon dual-write / RLS 068 / MPS-MRP 069 / stage-gate | ENG COMPLETE Wave 1 |
| Spec 030 Ollama degrade + roles + write-back 070 + Excel + A18–A20 stubs | ENG COMPLETE Wave 1 (8A) |

## Tags

| Tag | Status |
|-----|--------|
| v9.1.1-r2 | HOLD until G-R2-04 |
| v9.1.0-r2 | **Do not push** (stale) |
| v9.3.0-r1-eng | Not applied (COM CONDITIONAL) |
| v9.2.0-planning | Applied @ b04434d |

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
