# Data Model: Release Stabilization Entities

**Feature**: 002-release-stabilization-gates  
**Date**: 2026-06-21

This feature does not introduce database tables. It defines **process entities** for release governance and validation evidence.

---

## Entity: ReleaseGate

| Field | Type | Description |
|-------|------|-------------|
| `gate_id` | enum | `GATE_1`, `GATE_2`, `GATE_3` |
| `name` | string | Human-readable gate name |
| `phase` | enum | `A`, `B`, `C` |
| `entry_criteria` | list[string] | Prerequisites before starting |
| `exit_criteria` | list[string] | Required outcomes to pass |
| `status` | enum | `NOT_STARTED`, `IN_PROGRESS`, `PASSED`, `FAILED`, `WAIVED` |
| `owner_role` | string | Engineering, DevOps, Tech Lead |
| `started_at` | datetime | Optional |
| `completed_at` | datetime | Optional |
| `waived_reason` | string | Required if status = WAIVED |

**State transitions**:
```text
NOT_STARTED → IN_PROGRESS → PASSED
                         → FAILED → IN_PROGRESS (retry)
                         → WAIVED (requires sign-off)
```

---

## Entity: ValidationEvidence

| Field | Type | Description |
|-------|------|-------------|
| `evidence_id` | uuid | Unique identifier |
| `gate_id` | enum | Parent gate |
| `task_id` | string | e.g., `A2-001`, `B2-001` |
| `type` | enum | `TEST_LOG`, `SMOKE_OUTPUT`, `K6_REPORT`, `CHECKLIST`, `SCREENSHOT` |
| `artifact_path` | string | Relative path under `evidence/` |
| `summary` | string | One-line result |
| `passed` | boolean | Pass/fail |
| `recorded_at` | datetime | Timestamp |
| `recorded_by` | string | Engineer name or CI job ID |

**Validation rules**:
- Gate cannot pass unless all required evidence items have `passed = true`
- WAIVED gates require explicit `waived_reason` on gate + evidence gap documented

---

## Entity: CrossArtifactConflict

| Field | Type | Description |
|-------|------|-------------|
| `conflict_id` | string | e.g., `C1`, `H4` |
| `severity` | enum | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `source_artifact` | string | File path |
| `target_artifact` | string | File path |
| `description` | string | Mismatch summary |
| `resolution` | string | Fix applied |
| `resolved` | boolean | Reconciliation complete |
| `resolved_at` | datetime | Optional |

**Validation rules**:
- Gate 3 cannot pass while any CRITICAL or HIGH conflict has `resolved = false`

---

## Entity: ReadinessScore

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | e.g., `2026-06-21-gate2` |
| `overall` | integer | 0–100 |
| `dimensions` | map[string, int] | product, testing, security, ops, documentation |
| `baseline` | integer | Pre-stabilization (74) |
| `target` | integer | Post-Gate 2 (85) |
| `methodology` | string | How scores were derived |
| `published_in` | string | `READINESS.md` path |
| `supersedes` | list[string] | Deprecated scores (87, 90, 99) |

**Validation rules**:
- Only one `ReadinessScore` may be marked `published_in` at a time
- `overall` must equal weighted average of dimensions (document weights in READINESS.md)

---

## Entity: ReleaseTag

| Field | Type | Description |
|-------|------|-------------|
| `tag_name` | string | e.g., `v1.0.0-rc1` |
| `commit_sha` | string | Git SHA |
| `gate_2_evidence_id` | uuid | Link to E2E proof |
| `release_notes_path` | string | `RELEASE_NOTES.md` |
| `blocked_items` | list[string] | e.g., `C-007 Keycloak` |
| `created_at` | datetime | Tag date |

**Validation rules**:
- Tag requires Gate 2 PASSED
- `blocked_items` must be non-empty if any BLOCKED work remains (transparency)

---

## Relationships

```text
ReleaseGate 1──* ValidationEvidence
ReleaseGate 1──* CrossArtifactConflict (resolved in Gate 3)
ReadinessScore ── published after Gate 2
ReleaseTag ── requires Gate 2 PASSED
```
