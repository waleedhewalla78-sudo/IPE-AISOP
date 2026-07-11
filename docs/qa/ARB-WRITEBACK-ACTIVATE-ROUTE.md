# ARB Note — Write-back activate route (Spec 022 T023 / Spec 023 T022)

**Date:** 2026-07-11  
**Issues:** #71, #94

## Finding

`star-trans-validate.ps1` probed `POST /api/v1/activate`, which 404s.

Canonical connector route (router prefix `/sync/odoo` + `/activate`):

`POST /api/v1/sync/odoo/activate`

Implemented in `services/connector/app/api/v1/activate.py`.

## Resolution

Validate script updated to probe the canonical path. Kong customer profiles must route `/api/v1/sync/odoo/*` to connector (already typical for R1 sync paths). If a profile still 404s, add/confirm Kong route — do not invent a second bare `/activate` unless product requires alias.

## Live Odoo

Actual schedule write-back still requires PH1-02 staging credentials — COM OPEN.
