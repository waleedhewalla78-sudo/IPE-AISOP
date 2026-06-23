# D365 sandbox integration test (R4 T042)
$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot
python scripts/integration/d365_sandbox_validate.py @args
exit $LASTEXITCODE
