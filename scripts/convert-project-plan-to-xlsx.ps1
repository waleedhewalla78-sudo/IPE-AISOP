# Convert project-plan CSV to XLSX for Schedule upload
# Requires: Excel installed (COM) OR Python openpyxl
# Usage: .\scripts\convert-project-plan-to-xlsx.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Csv = Join-Path $Root "docs\demo-data\startrans\project-plan-startrans-w12.csv"
$Xlsx = Join-Path $Root "docs\demo-data\startrans\project-plan-startrans-w12.xlsx"

if (-not (Test-Path $Csv)) {
    Write-Host "Missing: $Csv" -ForegroundColor Red
    exit 1
}

# Try uv + openpyxl (preferred on this repo)
$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($uv) {
    uv run --with openpyxl python -c @"
import csv
from pathlib import Path
from openpyxl import Workbook
csv_path = Path(r'$Csv')
xlsx_path = Path(r'$Xlsx')
wb = Workbook()
ws = wb.active
ws.title = 'ProjectPlan'
with csv_path.open(newline='', encoding='utf-8') as f:
    for row in csv.reader(f):
        ws.append(row)
wb.save(xlsx_path)
print(f'Wrote {xlsx_path}')
"@
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Created $Xlsx" -ForegroundColor Green
        exit 0
    }
}

# Try Python openpyxl
$py = Get-Command python -ErrorAction SilentlyContinue
if ($py) {
    $script = @"
import csv
from pathlib import Path
try:
    from openpyxl import Workbook
except ImportError:
    raise SystemExit('openpyxl not installed: pip install openpyxl')

csv_path = Path(r'$Csv')
xlsx_path = Path(r'$Xlsx')
wb = Workbook()
ws = wb.active
ws.title = 'ProjectPlan'
with csv_path.open(newline='', encoding='utf-8') as f:
    for row in csv.reader(f):
        ws.append(row)
wb.save(xlsx_path)
print(f'Wrote {xlsx_path}')
"@
    $script | python -
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Created $Xlsx" -ForegroundColor Green
        exit 0
    }
}

# Fallback: Excel COM (Windows)
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $wb = $excel.Workbooks.Open($Csv)
    if (Test-Path $Xlsx) { Remove-Item $Xlsx -Force }
    $xlOpenXMLWorkbook = 51
    $wb.SaveAs($Xlsx, $xlOpenXMLWorkbook)
    $wb.Close($false)
    $excel.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
    Write-Host "Created $Xlsx (via Excel COM)" -ForegroundColor Green
    exit 0
} catch {
    Write-Host "Could not convert automatically." -ForegroundColor Red
    Write-Host "Manual: Open $Csv in Excel -> Save As .xlsx -> $Xlsx" -ForegroundColor Yellow
    exit 1
}
