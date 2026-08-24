# Star Trans tenant runbook (BATCH2-1)

## Provision (what Prompt 1 did)

1. Wrote `tenant-config.yml` (reference-customer, Cairo tz, EGP).
2. Added Alembic **087** `provision_startrans_tenant`.
3. On **lab** `ipe_test`: bound slug `star-trans` to existing seed tenant
   `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11`. Did **not** insert a second
   `cdm_tenant` (would split 28 MOs).
4. Stored HMAC **reference** only: `hetzner-secrets://ipe/tenants/star-trans/copilot-hmac`.
5. Inserted placeholder user `admin@startrans.eg` with `is_active=false` and
   **no password** (real users = BATCH2-4).

## Rollback if provisioning fails

```powershell
$env:IPE_DATABASE_URL_SYNC = "postgresql://ipe:ipe_test_pass@localhost:5433/ipe_test"
.\.venv\Scripts\python.exe -m alembic -c migrations\alembic.ini downgrade 086
```

`downgrade()` drops onboarding tables and the placeholder admin. It does **not**
delete the seeded Star Trans tenant or MOs.

## Add users

BATCH2-4 (`provision-users.py` + `config/users.yml`). Do not add convenience
accounts here.

## Disable tenant (contract termination)

```sql
UPDATE cdm_tenant SET is_active = false WHERE id = '<tenant-uuid>';
UPDATE cdm_tenant_onboarding SET config = config || '{"disabled": true}'::jsonb
 WHERE slug = 'star-trans';
```

Requires human + legal confirmation.

## Export tenant data (GDPR)

Use existing DSAR endpoints on dpe-svc (`/api/v1/dsar/...`) scoped by
`app.current_tenant_id`. Do not dump other tenants.

## Emergency contacts

| Role | Contact |
|------|---------|
| Diligent on-call | support@diligent.ai (placeholder) |
| Star Trans IT | TBD — not in repo |
| Production DB | Hetzner secrets manager — not in git |

## Production migration

**Blocked** until human confirmation. Never point `IPE_DATABASE_URL_SYNC` at
production from a Cursor agent session without an explicit go-ahead.
