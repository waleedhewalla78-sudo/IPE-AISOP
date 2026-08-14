# Converge — Spec 040 Star Trans Demo Aug 18

**Date:** 2026-08-14  
**Assessed:** codebase STREAM commits + Spec 040 artifacts vs warm-stack ops  

---

## Assessment summary

| Area | Spec/Plan expectation | Codebase | Gap |
|------|----------------------|----------|-----|
| Hygiene Streams 1 | FR-040-01…05 | Present | None eng |
| Excel Streams 2 | FR-040-14…17 | Present + template aligned | Live Kong upload not proven this session |
| IA Streams 3 | FR-040-06…07 | Present | None eng |
| Homes Streams 4 | FR-040-08…09 | Present | Needs live workspace API for demo polish |
| Gantt Streams 5 | FR-040-10 | Present | Needs active schedule data |
| Drawer Streams 6 | FR-040-11…13 | Present | None eng |
| Ops Streams 7 | FR-040-18 | Docs only | **Walkthrough boxes + PNGs open** |
| Speckit | feature.json → 040 | Set | — |

**Verdict:** Engineering for Spec 040 is **converged**. Remaining work is **ops/COM** — appended below as new tasks.

---

## Newly appended tasks (from converge)

### Ops (must finish before Mon 18 morning)

- [ ] **T090** Bring up R2: `docker compose -f infrastructure/docker/docker-compose.release2.yml up -d` until kong+web+dpe+fea+cap+upload healthy
- [ ] **T091** Reload Kong; confirm `curl`/browser `POST /api/v1/data/upload` through `:8000`
- [ ] **T092** Run `.\scripts\seed-startrans-demo.ps1` + optional `purge-widget-fixtures.sql`
- [ ] **T093** Execute all 8 steps in `docs/STAR-TRANS-DEMO-WALKTHROUGH.md` — tick PASS
- [ ] **T094** Capture 8 PNGs listed in `docs/star-trans-demo-screenshots/README.md`
- [ ] **T095** Send customer email (`CUSTOMER-EMAIL-DATA-TEMPLATE.md`) + attachment if not already sent
- [ ] **T096** If customer file returns Sunday: ingest via `/admin/data/upload`; re-run T093 risk/home checks
- [ ] **T097** Sun 17 18:00 hard stop — bugfix only; Mon 18 morning demo mode

### Eng harden (optional if time before Sun 18:00 — else defer post-demo)

- [ ] **T100** Playwright smoke: role switch Executive/Planner `/home`
- [ ] **T101** Map `06b_BOMLines` / `07b_RoutingOperations` into demo tables (currently preview-heavy)
- [ ] **T102** Promote `demo_*` → CDM commit path with RLS (post-demo; Principle I)
- [ ] **T103** Dedicated Supervisor/Buyer home layouts (currently Planner fallback)

### COM (never eng-close)

- [ ] **T110** OQ-7 pricing
- [ ] **T111** PH1-02 live Odoo
- [ ] **T112** G-R2-04 Arabic QA
- [ ] **T113** C-01…C-08 commercial

---

## Evidence helpers added this converge

- `scripts/verify-startrans-template.ps1` — PASS (24 sheets, 69 sample rows, priority OK)
- Spec 012 marked `superseded_for_aug18_demo: specs/040-startrans-demo-aug18`

## Stop

No further feature implementation in Spec 040 unless T100–T103 are explicitly pulled before Sunday freeze.
