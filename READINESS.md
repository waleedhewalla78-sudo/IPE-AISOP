# IPE Platform — Deployment Readiness

**Version**: v8.2.0  
**Published**: 2026-06-27  
**Supersedes**: v7.0.0, v6.1.0, v6.0.0, v1.0.0  
**Product spec**: [docs/PRD-IPE-COMPREHENSIVE-AS-IS.md](docs/PRD-IPE-COMPREHENSIVE-AS-IS.md)

---

## Overall Score: 100/100 (Speckit) · ~92/100 (Audit) · 32/32 demo

| Metric | Value |
|--------|-------|
| **Live demo** | **32/32** (30 core + sustain CP31 + quality CP32) |
| **Chaos** | **6/6** C1–C6 (post-v8 documented) |
| **Git tags** | v1.0.0 … v6.1.0; **v8.2.0 ready to tag** |
| **v8 integration** | **5/5** (`tests/integration/test_v8_e2e.py`) |
| **Phase** | **v8.2.0** — P1/P2 closed, POST-B scaffolds ready |
| **FR-P** | 13/14 — FR-P-13 Keycloak scaffolded (POST-B activation) |
| **LLM** | Ollama + OpenRouter + Anthropic fallback |

| Dimension | Score | Notes |
|-----------|-------|-------|
| Product completeness | 100 | v7 core + 8 v8 streams + sustain/quality demo |
| Testing | 96 | 870+ core; 180 dpe-svc; Playwright E2E foundation |
| Security | 82 | RBAC + RLS INSERT (035); Keycloak scaffold |
| Operations | 92 | Port map documented; health wait script |
| Documentation | 98 | DEPLOYMENT-READINESS-v8.2.0.md |

See `specs/010-v8-validation-convergence/analyze.md` for full open-points list.

---

## Phase completion

| Phase | Scope | Status |
|-------|-------|--------|
| 0–4 | v1.0.0 → v6.1.0 | ✅ Complete |
| 5 | v7.0.0 hub consolidation | ✅ Complete |
| 6 | v8 Phase 1 (U1–U3) | ✅ Validated |
| 7 | v8 Phase 2 (U4–U6) | ✅ Validated |
| 8 | v8 Phase 3 (U7–U8) | ✅ Validated |
| 9 | v8 validation sprint | ✅ QA-001–010 |
| 10 | v8.2.0 closure | ✅ P1/P2 + scaffolds |

---

## Production scaffolding (POST-B — plug-and-play)

| Component | Scaffold | Activation |
|-----------|----------|------------|
| Keycloak SSO | `ipe_shared/auth/keycloak.py` | `AUTH_PROVIDER=keycloak` |
| Secrets | `config/secrets_manager.py` | `SECRETS_PROVIDER=aws_sm\|hashi_vault` |
| Stripe billing | `ipe_shared/billing/stripe_adapter.py` | `BILLING_PROVIDER=stripe` |
| ERP connectors | `connector/app/erp/base.py` | `ERP_PROVIDER=sap\|d365` |
| RLS legacy INSERT | migration `035` | `alembic upgrade head` |

See `docs/DEPLOYMENT-READINESS-v8.2.0.md`.

---

## Production blockers (POST-B activation only)

| ID | Issue | Status |
|----|-------|--------|
| C-007 | Keycloak / enterprise IdP | Scaffold ready |
| SEC-P0 | Production JWT / secrets | Registry + audit script |
| BILL-P1 | Live Stripe | Mock + adapter scaffold |
| RLS-P1 | Legacy RLS INSERT | Migration 035 ready |
| ERP-P2 | Live SAP/D365 | Interface scaffolded |

---

## v8 deliverables — live proven

| Stream | Demo CP | Integration |
|--------|---------|-------------|
| U1 Copilot sessions | CP30 | ✅ |
| U2 Demand | CP21–22 | ✅ |
| U3 Scenario | CP23–24 | ✅ |
| U4 Supply | CP25 | ✅ (4 facilities seeded — migration 034) |
| U5 Orders | CP26 | ✅ |
| U6 Equipment | CP27 | ✅ |
| U7 Design AI | CP28 | ✅ |
| U8 Procurement | CP29 | ✅ |
| Sustain | CP31 | ✅ |
| Quality | CP32 | ✅ |

---

## Quick commands

```powershell
cd E:\AISOP\ipe
.\scripts\run-full-demo.ps1 -ReportPath docs\qa-e2e-demo-v8-report.txt
uv run pytest tests/integration/test_v8_e2e.py -m integration -v
```
