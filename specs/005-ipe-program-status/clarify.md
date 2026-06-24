# Clarify: IPE Program Status (005)

**Feature**: `005-ipe-program-status` | **Date**: 2026-06-23  
**Status**: Resolved — binding for release track RV-01–RV-05  
**Inputs**: [spec.md](./spec.md), [../004-ai-first-v6/clarify-v6.md](../004-ai-first-v6/clarify-v6.md), demo report `docs/demo-run-report-v6.txt`

---

## Resolved Decisions

| ID | Question | Decision | Rationale |
|----|----------|----------|-----------|
| C-P-01 | What is the active speckit feature? | **005** status rollup; **004** implementation | `.specify/feature.json` points 005 spec + 004 active_implementation |
| C-P-02 | What blocks v6.0.0 tag? | **Live demo 20/20** + stakeholder approval (T055) | Code 54/55; tag ≠ code (C-V6-08) |
| C-P-03 | Is launch-verify sufficient without Docker? | **Yes** for REL-TEST | Unit tests; stack required for REL-DEMO only |
| C-P-04 | Demo failure root cause (2026-06-23 14/20)? | **Stale stack + schedule timeout** | V6 routes 404 → rebuild images; CP4/15 timeout → ML per-op + all MOs |
| C-P-05 | Fix schedule demo timeout? | **Limit demo MOs to 3** in script + **ML timeout 0.2s** in cap-svc | Keeps OR-Tools path; no solver change |
| C-P-06 | 002 T049–T053 still required? | **Hygiene only** — T053 cancelled (003 v1.0.0 supersedes) | Non-blocking for v6.0.0 |
| C-P-07 | POST-A/B/C/D in scope now? | **No** — post-tag backlog | Implement only after REL-TAG |
| C-P-08 | GitHub issues without remote? | **GITHUB_ISSUES.md templates** + `create-release-issues.ps1` when `gh` + origin ready | Documented fallback |
| C-P-09 | Readiness authority | **READINESS.md 96/100** | Supersedes 85, 92, 99 in legacy docs |
| C-P-10 | Notion sync | **Repo wins on conflict** | Notion mirror; bulk sync after T055 |

---

## Underspecified Areas — Now Binding

### Release verification order

1. P-DOC (parallel, mostly done)
2. REL-STACK → REL-TEST → REL-DEMO → REL-TAG
3. REL-PROD optional for 100/100

### Demo checkpoint numbering

- Script labels CP **15** = 003 **checkpoint 16** (persist-after-approve). Documented in `004/quickstart.md` (P-DOC-06).

### Stakeholder gate (REL-12)

- Agent may complete RV-01–RV-03 and prepare tag command.
- **REL-13 tag execution requires explicit user approval** (no autonomous tag per git safety rules).

---

## Open (Unchanged)

| Item | Blocker | Feature |
|------|---------|---------|
| Keycloak live IdP | Azure AD sandbox | 002 C-007 |
| k6 200 VU + Chaos evidence | Ops time | 003 R4 / RV-05 |
| Stripe, mobile, WCAG | Product scope | POST-D |

---

**Next**: `/speckit.implement` REL-STACK through REL-DEMO; user approval for REL-TAG.
