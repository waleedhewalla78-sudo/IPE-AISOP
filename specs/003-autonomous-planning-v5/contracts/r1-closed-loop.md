# Contract: R1 Closed-Loop Scheduling

**Phase**: R1 | **Exit Gate**: Approve → persist → Kafka

## Verification Checklist

- [ ] G1 POST `/capacity/schedule` persists `ai_suggested_start/end` on MO and `planned_start/end` on work orders
- [ ] G2 GET `/capacity/schedule/active` returns Gantt rows matching last proposal/approval
- [ ] G3 POST `/capacity/schedule/approve` increments MO `version`; 409 on stale version
- [ ] G4 Kafka topic `ipe.schedule.approved` emitted with Avro envelope
- [ ] G5 Priority from `cdm_demand_line.priority_score` affects operation ordering
- [ ] G6 Demo script checkpoint 16 passes

## Evidence

Store logs in `specs/003-autonomous-planning-v5/evidence/r1/`
