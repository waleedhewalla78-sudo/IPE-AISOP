# Plan — 020 Planning Intelligence

## Architecture

Extend existing services; add `sop-svc` only for the S&OP process engine.

```
Odoo 19 ──connector──→ CDM
                         ├── demand-svc (forecast quality, ARIMA/best-fit)
                         ├── mat-svc (segmentation, safety stock)
                         ├── cap-svc (utilisation alerts)
                         └── sop-svc (cycles, consensus, versions)
                                   └── nlp-svc Copilot tools
```

## Migration chain

`042` → `044` segmentation → `045` forecast quality → `046` connector extensions → `047` safety stock → `048` capacity alerts → `049` sop engine

Note: Spec docs numbered 043–048; repo already has `043_odoo_config_versioning`, so numbers shifted +1 from Module A onward while keeping Module B as 044.

## Build order

1. B → A → D → Odoo → C → E → F → Copilot → Docker/Kong → tests → docs → commit/push

## Honest blockers

- Live Odoo 19 customer instance: use mock XML-RPC / protocol stand-ins in tests
- statsmodels/scipy: add as service dependencies; graceful SES fallback if missing
