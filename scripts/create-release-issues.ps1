# Create GitHub issues for IPE V6 release track
# Requires: gh CLI, git remote 'origin'
# Usage: .\scripts\create-release-issues.ps1

$ErrorActionPreference = "Stop"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "GitHub CLI (gh) not found. Install from https://cli.github.com/ and run gh auth login"
}

$remote = git remote get-url origin 2>$null
if (-not $remote) {
    Write-Error "No git remote 'origin'. Add: git remote add origin https://github.com/ORG/REPO.git"
}

$issues = @(
    @{
        Title = "[REL-STACK] Docker stack up + seed demo tenant"
        Labels = "release,P0,ops"
        Body = @"
## Summary
Bring up IPE docker stack and seed V6 demo data.

## Checklist
- [ ] REL-01 docker compose config
- [ ] REL-02 docker compose up -d
- [ ] REL-03 API :8000/health
- [ ] REL-04 migrations through 027
- [ ] REL-05 seed-demo-client.ps1

Ref: specs/004-ai-first-v6/tasks-release.md
"@
    },
    @{
        Title = "[REL-TEST] launch-verify.ps1 10/10"
        Labels = "release,P0,testing"
        Body = @"
## Summary
Backend test matrix — 10 services.

## Status
- [x] REL-06 10/10 passed 2026-06-23
- [x] REL-08 evidence: specs/004-ai-first-v6/evidence/rv-02-launch-verify.txt

Ref: specs/004-ai-first-v6/GITHUB_ISSUES.md
"@
    },
    @{
        Title = "[REL-DEMO] run-full-demo.ps1 20/20"
        Labels = "release,P0,demo"
        Body = @"
## Summary
Live demo including V6 CP17–20.

## Command
.\scripts\run-full-demo.ps1 -ReportPath docs\demo-run-report-v6.txt

Depends on: REL-STACK
"@
    },
    @{
        Title = "[REL-TAG] Git tag v6.0.0 (T055)"
        Labels = "release,P0,tag"
        Body = @"
## Summary
Tag v6.0.0 after demo 20/20 + stakeholder approval.

Depends on: REL-DEMO
"@
    },
    @{
        Title = "[P-DOC] Speckit documentation sync"
        Labels = "docs,P1"
        Body = @"
## Summary
Resolve cross-artifact drift from analyze-v6.md.

Ref: tasks-release.md P-DOC-01–08
"@
    },
    @{
        Title = "[REL-PROD] k6 + Chaos → READINESS 100/100"
        Labels = "production,P2,performance"
        Body = @"
## Summary
Optional production hardening evidence.

Depends on: REL-TAG
"@
    }
)

foreach ($issue in $issues) {
    Write-Host "Creating: $($issue.Title)"
    gh issue create --title $issue.Title --body $issue.Body --label $issue.Labels
}

Write-Host "Done. View issues: gh issue list --label release"
