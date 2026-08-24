# T091 Kong Upload Live â€” 2026-08-15

## Routes
Confirmed in `infrastructure/docker/kong.release2.yml`: `/api/v1/upload` and `/api/v1/data`.

## Results
| Check | Result |
|-------|--------|
| Unauth POST via Kong :8000 | HTTP **200** |
| Authenticated via Kong | Skipped this run (JWT password login blocked by agent policy; use critical_path RS256 path for auth e2e) |
| Direct upload-svc :8120 multipart | HTTP **200** â€” sheets_found=24 insert=69 valid=True |
| Non-xlsx via upload-svc | HTTP **200** |

## Preview quality
- Expected 24 sheets; observed sheets_found=24
- will_insert=69 valid=True

## VERDICT
**YELLOW**
