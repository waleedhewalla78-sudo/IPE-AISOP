# Contract: V6-R4 — Predictive Maintenance & MDR Auto-Correction

**Phase**: V6-R4 | **Tasks**: T037–T045 | **Exit**: SC-V6-04

---

## API Contracts

### POST `/api/v1/iot/telemetry`

**Body**:

```json
{
  "machine_id": "CNC-04",
  "rul_hours": 36,
  "vibration_rms": 2.1,
  "recorded_at": "2026-06-23T10:00:00Z"
}
```

**When** `rul_hours < 48`: publish `ipe.maintenance.block_required`

---

## Kafka: `ipe.maintenance.block_required`

**Schema**: `ipe_maintenance_block_required.avsc`

```json
{
  "tenant_id": "uuid",
  "machine_id": "CNC-04",
  "work_center_id": "uuid",
  "block_start": "2026-06-24T08:00:00Z",
  "block_end": "2026-06-25T08:00:00Z",
  "rul_hours": 36
}
```

**Consumer**: cap-svc — inject calendar block, trigger partial re-solve

---

## Database: `cdm_machine_health_telemetry`

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID (RLS) |
| machine_id | text |
| work_center_id | UUID |
| rul_hours | numeric |
| vibration_rms | numeric nullable |
| last_seen_at | timestamptz |

---

## MDR Auto-Correction Draft

### Connector action: `sync_routing_correction`

**Payload**:

```json
{
  "routing_id": "uuid",
  "operation_id": "uuid",
  "standard_time_before_mins": 45,
  "standard_time_after_mins": 52,
  "deviation_pct": 15.6,
  "status": "pending_approval"
}
```

**Reject**: audit only; MDR score unchanged

---

## Acceptance Tests

| ID | Test |
|----|------|
| AC-R4-01 | RUL 36h → block + reschedule within 60s |
| AC-R4-02 | No alternate WC → feasibility queue constraint |
| AC-R4-03 | 15% deviation → routing draft in queue |
| AC-R4-04 | Demo checkpoint 20 passes |
