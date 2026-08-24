# Star Trans tenant pack — README (BATCH2-1)

Lab-first onboarding pack. **Not** Hetzner production until a human applies
migration 087 on the production database.

## Identity

| Field | Value |
|-------|--------|
| Slug | `star-trans` |
| Canonical UUID (uuid5) | `6a7281ee-62cb-5a72-8162-d3c573e54877` |
| Lab tenant (seed) | `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11` |

## Apply on lab (already authorized for Batch 2 scaffold)

```powershell
cd e:\AISOP\ipe
$env:IPE_DATABASE_URL_SYNC = "postgresql://ipe:ipe_test_pass@localhost:5433/ipe_test"
.\.venv\Scripts\python.exe -m alembic -c migrations\alembic.ini upgrade head
```

## Production

Do **not** run `alembic upgrade` against Hetzner until:

1. Batch 1 PR 164 is merged (currently OPEN)
2. SOW countersign is on file
3. A human confirms production DB URL

See `RUNBOOK.md`.
