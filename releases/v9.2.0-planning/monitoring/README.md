# IPE Health Monitoring

Checks Release 1 service health endpoints and PostgreSQL readiness. Logs warnings when unhealthy.

## Linux

```bash
chmod +x scripts/monitoring/ipe-health-check.sh scripts/monitoring/setup-monitoring.sh

# Manual
./scripts/monitoring/ipe-health-check.sh /var/log/ipe-health.log

# Cron every 5 minutes
./scripts/monitoring/setup-monitoring.sh
```

## Windows

```powershell
.\scripts\monitoring\ipe-health-check.ps1 -LogPath C:\ipe\logs\health.log

# Task Scheduler (Administrator once):
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\ipe\scripts\monitoring\ipe-health-check.ps1"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration ([TimeSpan]::MaxValue)
Register-ScheduledTask -TaskName "IPE-Health-Check" -Action $action -Trigger $trigger -RunLevel Highest
```

## Endpoints checked

| Service | Port | Path |
|---------|------|------|
| dpe-svc | 8001 | `/api/v1/health` (fallback `/healthz`) |
| fea-svc | 8004 | same |
| res-svc | 8005 | same |
| cap-svc | 8003 | same |
| mat-svc | 8002 | same |
| connector | 8009 | same |
| PostgreSQL | compose `db` | `pg_isready -U ipe` |

## Optional webhook

Set `IPE_HEALTH_WEBHOOK` to a WhatsApp/Teams/Slack webhook URL to receive failure notifications.
