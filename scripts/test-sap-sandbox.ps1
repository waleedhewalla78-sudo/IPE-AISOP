# SAP sandbox integration test (R4 T041)
$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot
python scripts/integration/sap_sandbox_validate.py @args
exit $LASTEXITCODE
