"""Data retention policy configuration (P9-009).

Defines retention periods and actions for CDM and GDPR tables.
Actions: archive (copy to archive table then delete), anonymize (replace PII
columns with [ANONYMIZED]), delete (hard delete).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ActionType = Literal["archive", "anonymize", "delete"]


@dataclass(frozen=True)
class RetentionPolicy:
    entity_type: str
    retention_days: int
    action: ActionType
    archive_table: str | None = None


DEFAULT_RETENTION_POLICIES: dict[str, RetentionPolicy] = {
    "cdm_audit_log": RetentionPolicy(
        entity_type="cdm_audit_log",
        retention_days=2555,
        action="archive",
        archive_table="cdm_audit_log_archive",
    ),
    "cdm_delay_event": RetentionPolicy(
        entity_type="cdm_delay_event",
        retention_days=1095,
        action="archive",
        archive_table="cdm_delay_event_archive",
    ),
    "cdm_mdr_score": RetentionPolicy(
        entity_type="cdm_mdr_score",
        retention_days=730,
        action="anonymize",
    ),
    "cdm_demand_line": RetentionPolicy(
        entity_type="cdm_demand_line",
        retention_days=1825,
        action="archive",
        archive_table="cdm_demand_line_archive",
    ),
    "cdm_manufacturing_order": RetentionPolicy(
        entity_type="cdm_manufacturing_order",
        retention_days=1825,
        action="archive",
        archive_table="cdm_manufacturing_order_archive",
    ),
    "gdpr_dsar_request": RetentionPolicy(
        entity_type="gdpr_dsar_request",
        retention_days=30,
        action="delete",
    ),
    "gdpr_consent": RetentionPolicy(
        entity_type="gdpr_consent",
        retention_days=2555,
        action="archive",
        archive_table="gdpr_consent_archive",
    ),
}


def get_retention_policy(entity_type: str) -> RetentionPolicy | None:
    return DEFAULT_RETENTION_POLICIES.get(entity_type)


def get_all_policies() -> dict[str, RetentionPolicy]:
    return dict(DEFAULT_RETENTION_POLICIES)
