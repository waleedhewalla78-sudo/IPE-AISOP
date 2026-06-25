# Clarify: IPE Program Status (005)

**Feature**: `005-ipe-program-status` | **Updated**: 2026-06-25  
**Status**: Resolved — binding for release track REL-* and POST-* backlog  
**Inputs**: [spec.md](./spec.md), [../004-ai-first-v6/clarify-v6.md](../004-ai-first-v6/clarify-v6.md), [analyze.md](./analyze.md), `docs/demo-run-report-v6.txt`, `docs/rel-demo-stack.log`

---

## Session 2026-06-26 — Resolved (demo fixes + master plan)

| ID | Question | Decision | Rationale |
|----|----------|----------|-----------|
| C-P-26 | CP10/11 Copilot 503 root cause? | **`query_llm()` raises** `LLMUnavailableError`; orchestrator must catch before structured fallback | Not Kong routing; fixed in `nlp-svc/.../orchestrator.py` |
| C-P-27 | CP15 persist failure root cause? | **85% feasibility guardrail** on low-score demo MOs + wrong `$ApproveMoIds` in script | Use MO-DEMO-005/006 (≥85%); not BUG-01 alone |
| C-P-28 | CP15 intermittent 500 after CP20? | **Synthetic MAINT_* op IDs** in solver assignments → `UUID()` parse error in `persist_schedule_proposal` | Skip non-UUID assignments (T021) |
| C-P-29 | CP18 tariff 500 root cause? | **`BomLine.tenant_id`** does not exist — join **`BillOfMaterial`** for tenant scope | Same class as T018 audit C-01 pattern |
| C-P-30 | CP20 recovery-plan 500 root cause? | **`alert-svc` never called `init_database()`** on lifespan | `recovery-plan` uses `get_session()` |
| C-P-31 | CP20 empty recovery options? | **No `cdm_disruption_event` seed** + early empty return | Seed + fallback to top proposed scenarios |
| C-P-32 | Phase 0 git before tag? | **Initial commit required** before `v6.0.0`; user must approve commit/tag | Master plan §5; C-P-16 unchanged |
| C-P-33 | CP15 pass criteria when Kafka down? | **CDM persist + `activated_count ≥ 1`** is demo gate; `success=false` + `erp_event_published=false` acceptable | BUG-01 semantics; demo script updated 2026-06-26 |

---

## Session 2026-06-25 — Resolved (batch, continued)

| ID | Question | Decision | Rationale |
|----|----------|----------|-----------|
| C-P-19 | Program product scope? | **IPE AISOP only** | User directive: neglect Nexus; canonical code in `ipe/` |
| C-P-20 | Nexus paths on disk? | **`E:\nexus-social-platform\`** exists; **`E:\AISOP\nexus-social/`** accidental — ignore | Disk search 2026-06-25; not in release path |
| C-P-21 | Demo login canonical? | **`Ahmed@nour` / `admin`** for scripts; **`admin@demo.com` / `demo`** for UI guide | Both in seed; script uses Ahmed |
| C-P-22 | V6 404 root cause confirmed? | **Missing app containers + Kong** — not missing FRs | Infra (db/redis/kafka) up; app images building |
| C-P-23 | Full vs lean compose? | **Lean demo overlay is default** for REL-STACK | Full compose blocked on Ollama pull (~500MB) |
| C-P-24 | Seed `gen_salt` failure? | **`CREATE EXTENSION pgcrypto`** prepended in `seed-data.ps1` | Required for bcrypt in seed SQL |
| C-P-25 | Integration 17 fail without Docker? | **41 pass / 8 fail live** — WS + sustain/quality out of demo stack | See `docs/integration-report-live.txt` |

---

## Session 2026-06-25 — Resolved (batch)

| ID | Question | Decision | Rationale |
|----|----------|----------|-----------|
| C-P-11 | Canonical repo layout? | **`E:\AISOP`** workspace; **`ipe/`** monorepo; root **`services/`** is orphan | READINESS.md + AGENTS.md |
| C-P-12 | Spec Kit location? | **`.specify/` at `E:\AISOP` root**; `feature.json` points to `ipe/specs/005-*` | User directive; no `my-project/` subfolder |
| C-P-13 | REL-STACK strategy? | **`docker-compose.demo.yml`** + **`scripts/rel-demo-stack.ps1`** | Skips ollama/airflow/keycloak; nlp-svc runs without Ollama dep |
| C-P-14 | Why demo 14/20 with V6 404? | **Stale/missing Docker images** — routes exist in code + kong.yml | Rebuild stack + seed; not missing FRs |
| C-P-15 | Demo schedule timeout (CP4/15)? | **Limit to 3 demo MOs** + cap ML timeout 0.2s | Already in `run-full-demo.ps1`; rebuild cap-svc image |
| C-P-16 | Git state at workspace root? | **No commits yet** on `master`; all files untracked | Use `git -c safe.directory=E:/AISOP` until safe.directory set |
| C-P-17 | When is 96/100 "done"? | **Code + docs** at 96; **live demo + tag** required for release claim | Tag ≠ implementation (C-V6-08) |
| C-P-18 | POST-* vs v6.0.0 scope? | **POST-* deferred until after REL-TAG** | clarify C-P-07 unchanged |

---

## Coverage Taxonomy (2026-06-25)

| Category | Status | Notes |
|----------|--------|-------|
| Functional scope & behavior | **Clear** | FR-P-01–14 in spec.md; IPE-only scope |
| Domain & data model | **Clear** | CDM + migrations 001–027 documented in 004 contracts |
| UX / interaction flows | **Partial** | 20 demo CPs defined; WCAG/mobile deferred POST-D |
| Non-functional (perf) | **Partial** | CPM <2s, k6 200 VU scripted not proven |
| Security & privacy | **Partial** | JWT demo OK; Keycloak live **BLOCKED** |
| Integration / ERP | **Partial** | Odoo connector live; SAP/D365 mapper-only |
| Edge cases | **Clear** | 85% guardrail, heuristic fallback, demo MO scope |
| Completion signals | **Clear** | REL-* phases + demo report |

**Outstanding (low impact, deferred to plan)**: ISO 27001 ISMS docs, feature store, Phoenix commerce.

---

## Resolved Decisions (prior sessions)

| ID | Question | Decision |
|----|----------|----------|
| C-P-01 | Active speckit feature? | **005** rollup; **004** implementation |
| C-P-02 | Blocks v6.0.0 tag? | **Demo 20/20** + approval (T055) |
| C-P-03 | launch-verify without Docker? | **Yes** for REL-TEST |
| C-P-04 | Demo 14/20 root cause? | Stale stack + schedule timeout |
| C-P-05 | Schedule timeout fix? | 3 demo MOs + ML timeout |
| C-P-06 | 002 T049–T053 required? | Hygiene only; T053 cancelled |
| C-P-07 | POST-A/B/C/D now? | No — post-tag |
| C-P-08 | GitHub issues without remote? | GITHUB_ISSUES.md templates |
| C-P-09 | Readiness authority | READINESS.md **96/100** |
| C-P-10 | Notion sync | Repo wins on conflict |

---

## Release verification order (binding)

1. P-DOC (parallel)
2. **REL-STACK** → REL-TEST → REL-DEMO → REL-TAG
3. REL-PROD optional (100/100)

### Stakeholder gate (REL-12)

- Agent may complete REL-01–REL-11 and prepare tag command.
- **REL-13 tag execution requires explicit user approval.**

---

## Open (unchanged)

| Item | Blocker | Track |
|------|---------|-------|
| Keycloak live IdP | Azure AD sandbox | POST-B1 / C-007 |
| k6 200 VU + Chaos | Ops time | REL-PROD |
| Stripe, mobile, WCAG | Product scope | POST-D |

**Next**: Complete REL-STACK via `rel-demo-stack.ps1`; user approval for REL-TAG.
