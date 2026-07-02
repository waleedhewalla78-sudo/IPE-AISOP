# Clarify — 009 v8 Phase 3

| Question | Decision |
|----------|----------|
| Where does Design AI UI live? | AI & Governance hub (alongside Copilot/trust) |
| Where does Procurement UI live? | Supply Chain hub |
| New ports? | material-svc **8090**, procurement-svc **8100** |
| Supplier model changes? | Add `esg_score`, `risk_tier`, `category` via migration 031 |
| Seed data strategy? | Lazy seed on first API call per tenant (catalog, spend, rules) |
