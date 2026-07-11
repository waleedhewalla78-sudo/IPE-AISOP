# IPE Backup Automation

Daily PostgreSQL backups for Star Trans / customer deployments. Custom-format (`pg_dump -Fc`), 7-day retention.

## Linux

```bash
chmod +x scripts/backup/ipe-backup.sh scripts/backup/setup-backup-schedule.sh

# Manual run
./scripts/backup/ipe-backup.sh /var/backups/ipe

# Install cron (daily 02:00)
./scripts/backup/setup-backup-schedule.sh
```

Optional: set `COMPOSE_DIR` if compose is not at `deploy/star-trans/`:

```bash
export COMPOSE_DIR=/opt/ipe-startrans
./scripts/backup/ipe-backup.sh /var/backups/ipe
```

## Windows

```powershell
# Manual run
.\scripts\backup\ipe-backup.ps1 -BackupDir C:\ipe\backups

# Task Scheduler (run as Administrator once):
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\ipe\scripts\backup\ipe-backup.ps1 -BackupDir C:\ipe\backups"
$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
Register-ScheduledTask -TaskName "IPE-Daily-Backup" -Action $action -Trigger $trigger -RunLevel Highest
```

## Restore

```bash
docker compose exec -T db pg_restore -U ipe -d ipe --clean --if-exists < /var/backups/ipe/ipe-backup-YYYY-MM-DD.dump
```

## Logs

Each run appends to `backup.log` in the backup directory (`SUCCESS` or `ERROR` with timestamp).
