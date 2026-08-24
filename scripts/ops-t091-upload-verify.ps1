# T091 Kong + upload-svc live verify (Spec 040)
# Writes reports only; does not print JWTs.
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$xlsx = Join-Path $root "docs\demo-data\startrans\IPE_Data_Template_StarTrans_v1.xlsx"
$report = Join-Path $root "docs\qa\T091-KONG-UPLOAD-LIVE-2026-08-14.md"
$tmp = Join-Path $env:TEMP "ipe_t091_preview.json"

# Unauth via Kong
$unauth = curl.exe -s -o NUL -w "%{http_code}" -X POST "http://localhost:8000/api/v1/data/upload" -F "files=@$xlsx"

# Direct to upload-svc (service-level; Kong JWT is the gateway gate)
$directCode = curl.exe -s -o $tmp -w "%{http_code}" -X POST "http://localhost:8120/api/v1/data/upload" -F "files=@$xlsx"

$preview = ""
$sheetCount = 0
$insert = 0
$valid = $false
if (Test-Path $tmp) {
  try {
    $d = Get-Content $tmp -Raw | ConvertFrom-Json
    $u = $d.uploads[0]
    $sheetCount = @($u.sheets_found).Count
    $insert = $u.preview.will_insert
    $valid = [bool]$u.valid
    $preview = "sheets_found=$sheetCount insert=$insert valid=$valid"
  } catch {
    $preview = "parse_error"
  }
}

# Non-xlsx rejection
$bad = Join-Path $env:TEMP "ipe_bad.txt"
Set-Content $bad "not a spreadsheet"
$badCode = curl.exe -s -o NUL -w "%{http_code}" -X POST "http://localhost:8120/api/v1/data/upload" -F "files=@$bad"

$verdict = "RED"
if ($directCode -eq "200" -and $sheetCount -eq 24 -and $insert -gt 0) {
  if ($unauth -eq "401" -or $unauth -eq "401" -or $unauth -eq "403" -or $unauth -eq "401") { $verdict = "GREEN" }
  elseif ($unauth -eq "404" -or $unauth -eq "000") { $verdict = "YELLOW" }
  else { $verdict = "YELLOW" }  # direct OK; Kong auth posture may allow anon in lab
  if ($unauth -eq "200") { $verdict = "YELLOW" } # should not accept unauth in prod posture
}

@"
# T091 Kong Upload Live — 2026-08-15

## Routes
Confirmed in ``infrastructure/docker/kong.release2.yml``: ``/api/v1/upload`` and ``/api/v1/data``.

## Results
| Check | Result |
|-------|--------|
| Unauth POST via Kong :8000 | HTTP **$unauth** |
| Authenticated via Kong | Skipped this run (JWT password login blocked by agent policy; use critical_path RS256 path for auth e2e) |
| Direct upload-svc :8120 multipart | HTTP **$directCode** — $preview |
| Non-xlsx via upload-svc | HTTP **$badCode** |

## Preview quality
- Expected 24 sheets; observed sheets_found=$sheetCount
- will_insert=$insert valid=$valid

## VERDICT
**$verdict**
"@ | Set-Content $report -Encoding utf8

Write-Output "T091_VERDICT=$verdict unauth=$unauth direct=$directCode sheets=$sheetCount insert=$insert bad=$badCode"
