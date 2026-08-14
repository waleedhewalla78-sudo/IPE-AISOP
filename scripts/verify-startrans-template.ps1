# Verify Star Trans Excel template parses (Spec 040 T065 helper)
# Usage: from ipe/  .\scripts\verify-startrans-template.ps1

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
$xlsx = Join-Path $root "docs\demo-data\startrans\IPE_Data_Template_StarTrans_v1.xlsx"
$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $xlsx)) { throw "Missing template: $xlsx" }
if (-not (Test-Path $py)) { throw "Missing venv python: $py" }

$env:PYTHONPATH = Join-Path $root "services\upload-svc"
$xlsxPosix = $xlsx.Replace('\','/')
$code = @"
from pathlib import Path
from app.core.startrans_workbook import parse_workbook, preview_counts, PRIORITY_SHEETS, EXPECTED_SHEETS
p = Path(r'$xlsxPosix')
r = parse_workbook(p.read_bytes(), p.name)
pr = preview_counts(r)
assert len(EXPECTED_SHEETS) == 24
assert not r.sheets_missing, r.sheets_missing
assert r.valid
print('PASS sheets', len(EXPECTED_SHEETS), 'insert', pr['will_insert'], 'fail', pr['will_fail'])
for s in PRIORITY_SHEETS:
    n = len(r.sheet_results[s].rows)
    print(f'  {s}: {n} rows')
"@
& $py -c $code
if ($LASTEXITCODE -ne 0) { throw "Template verify failed" }
Write-Host "Star Trans template verify OK"
