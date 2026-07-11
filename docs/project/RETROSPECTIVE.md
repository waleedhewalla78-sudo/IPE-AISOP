# IPE Project Retrospective

**Date:** 2026-07-11  
**Audience:** Internal engineering (not customer-facing)

---

## Project Metrics (workspace snapshot)

| Metric | Value |
|--------|------:|
| Python lines (`services/**/*.py`) | 64,618 |
| TypeScript lines (`apps/web/src/**/*.ts*`) | 11,194 |
| Backend test files | 249 |
| Frontend test files | 17 |
| Database migrations | 49 |
| Microservices | 29 |
| Spec directories | 23 |
| Documentation files (`docs/**/*.md`) | 130 |

---

## What Worked

- **Cursor as development tool:** Consistent code generation, pattern replication across services, rapid iteration across Sprint 1–3 closure
- **Constitution-driven development:** Principles enforced structure and quality from day one
- **Test-first approach:** Large automated suite caught regressions before integration
- **Release profile system:** R1/R2/full profiles enable graduated deployment without code forks
- **RLS from day one:** Tenant isolation never had to be retrofitted — it was structural
- **Sprint-based closure:** 3-sprint plan converted open-ended backlog into bounded, completable work (tags → customer enablement → dry-run/package/closure)

---

## What Created Unnecessary Complexity

- **Many microservices for zero customers:** A monolith + 2–3 services would have served Star Trans equally well. The microservices architecture is correct for 10+ customers but over-built for customer zero.
- **Kafka event streaming:** Never used by a customer. Batch sync (15-min Odoo sync) is sufficient for mid-market.
- **Keycloak scaffold:** Never completed to production. Local JWT is sufficient and simpler for R1.
- **Kind K8s cluster:** Useful for enterprise demos but created maintenance burden (migration parity, pod crashes, HPA conflicts).
- **Migration numbering divergence:** Spec plans said 043–048, actual repo used 044–049 due to prior migrations. Not a bug but creates confusion.

---

## What We'd Do Differently for Customer 2

- Start SOW negotiation before engineering is "complete"
- Deploy R1 profile only — don't show R2 until customer asks
- Hire Arabic reviewer before building Arabic UI
- Build implementation playbook from Customer 1 experience, not only from spec
- Scope the first engagement to ~4 weeks of deploy/train/support, not 6 months of feature development before contract

---

## Technical Debt Carried Forward

| Item | Effort | Priority |
|------|--------|----------|
| Keycloak SSO production | 3–4 weeks | P0 for enterprise |
| Structured JSON logging | 2 weeks | P1 |
| Prometheus metrics | 2 weeks | P1 |
| Distributed tracing (OTEL) | 2 weeks | P2 |
| Circuit breakers | 1 week | P2 |
| Graceful shutdown (SIGTERM) | 1 week | P2 |

---

## First Hire Onboarding Checklist

1. Read `constitution.md` (`.specify/memory/`) and `docs/PRD-IPE-AUTHORITATIVE.md`
2. Understand release profiles (R1/R2/full) — they control nav and compose
3. Deploy using `deploy/star-trans/` (or `releases/v9.2.0-planning/`) to understand the stack
4. Run full test suite before making any changes
5. Every table needs `tenant_id` + RLS — no exceptions
6. Follow existing code patterns in the target service — read before writing
7. Ask Waleed about business context; commercial blockers (OQ-7, Odoo access, Arabic sign-off) are not engineering inventables

---

## Sprint Closure Summary

| Sprint | Outcome |
|--------|---------|
| 1 | Tags cut (`v9.2.0-planning`), tests green, timeout fixes |
| 2 | SOW, sales materials, playbook, field mapping, validation script |
| 3 | Dry-run, demo seed, backup/monitoring, customer package, archive, retrospective |

**Engineering: DONE.** Remaining work is commercial only.
