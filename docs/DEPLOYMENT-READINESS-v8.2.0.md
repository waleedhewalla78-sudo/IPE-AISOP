# IPE v8.2.0 — Deployment Readiness Report

**Date:** 2026-06-28

## Staging / UAT / Client Demo Status: ✅ READY

### What Works

- **32/32** demo checkpoints (30 core + 2 extended: sustain + quality)
- **870+** unit tests + **180** dpe-svc tests + **5** integration + **28** frontend Vitest
- **6/6** chaos validated (v7 baseline; post-v8 re-run documented)
- Prophet/LSTM forecaster factory operational (SES fallback when libs unavailable)
- Supply→demand confidence adjustment scaffold (`ipe.supply.network.updated`)
- **22** services, Kong gateway, RLS WITH CHECK on v8 + legacy tenant tables (migration 035)
- Production scaffolds: Keycloak, secrets registry, Stripe adapter, ERP connector interface

### Production Checklist (POST-B)

- [ ] Keycloak SSO — scaffold ready, needs live instance + user sync
- [ ] Secrets Manager — registry complete, needs AWS SM or Vault config
- [ ] Stripe Billing — adapter scaffold ready, needs live keys + webhook
- [ ] RLS on legacy tables — migration 035 ready, apply + verify in prod
- [ ] SAP/D365 Connectors — interface scaffolded, needs live credentials
- [ ] WCAG 2.1 AA audit — not started
- [ ] Alertmanager/PagerDuty — not started

### Known Limitations for Staging

- SES/Prophet/LSTM forecasters use synthetic training in demo when history is thin
- Supply network uses seeded demo data (migration 034)
- Billing is mock (`BILLING_PROVIDER=mock`)
- Auth is local JWT (`AUTH_PROVIDER=local`)

### Verification Commands

```bash
./scripts/wait-for-healthy-stack.sh 120
pwsh scripts/run-full-demo.ps1 -ReportPath docs/qa-e2e-demo-final.txt
pytest services/demand-svc/tests/ -v -k forecaster
pytest services/shared/tests/test_auth_keycloak.py services/shared/tests/test_billing_adapter.py -v
```
