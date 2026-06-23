"""Usage metering for IPE SaaS billing.

Tracks API calls, user seats, storage, and compute minutes per tenant per period.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime

from ipe_shared.billing.pricing import MeteredResource

logger = logging.getLogger("ipe.billing.metering")


@dataclass
class MeteringSnapshot:
    tenant_id: str
    period_start: str
    period_end: str
    api_calls: int = 0
    user_seats: int = 0
    storage_gb: int = 0
    compute_minutes: int = 0
    recorded_at: str = ""

    def __post_init__(self) -> None:
        if not self.recorded_at:
            self.recorded_at = datetime.now(UTC).isoformat()

    def to_usage_dict(self) -> dict[str, int]:
        return {
            MeteredResource.API_CALLS.value: self.api_calls,
            MeteredResource.USER_SEATS.value: self.user_seats,
            MeteredResource.STORAGE_GB.value: self.storage_gb,
            MeteredResource.COMPUTE_MINUTES.value: self.compute_minutes,
        }


class UsageMeter:
    def __init__(self) -> None:
        self._counters: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def _period_key(self, tenant_id: str) -> str:
        now = datetime.now(UTC)
        return f"{tenant_id}:{now.year}:{now.month:02d}"

    def record_api_call(self, tenant_id: str, count: int = 1) -> None:
        key = self._period_key(tenant_id)
        self._counters[key][MeteredResource.API_CALLS.value] += count

    def record_user_seat(self, tenant_id: str, count: int = 1) -> None:
        key = self._period_key(tenant_id)
        self._counters[key][MeteredResource.USER_SEATS.value] = max(
            self._counters[key][MeteredResource.USER_SEATS.value], count
        )

    def record_storage(self, tenant_id: str, gb: float) -> None:
        key = self._period_key(tenant_id)
        self._counters[key][MeteredResource.STORAGE_GB.value] = max(
            self._counters[key][MeteredResource.STORAGE_GB.value], int(gb)
        )

    def record_compute_minutes(self, tenant_id: str, minutes: int) -> None:
        key = self._period_key(tenant_id)
        self._counters[key][MeteredResource.COMPUTE_MINUTES.value] += minutes

    def get_snapshot(self, tenant_id: str) -> MeteringSnapshot:
        key = self._period_key(tenant_id)
        now = datetime.now(UTC)
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            period_end = period_start.replace(year=now.year + 1, month=1)
        else:
            period_end = period_start.replace(month=now.month + 1)

        counters = self._counters[key]
        return MeteringSnapshot(
            tenant_id=tenant_id,
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            api_calls=counters.get(MeteredResource.API_CALLS.value, 0),
            user_seats=counters.get(MeteredResource.USER_SEATS.value, 0),
            storage_gb=counters.get(MeteredResource.STORAGE_GB.value, 0),
            compute_minutes=counters.get(MeteredResource.COMPUTE_MINUTES.value, 0),
        )

    def reset_period(self, tenant_id: str) -> None:
        key = self._period_key(tenant_id)
        self._counters[key] = defaultdict(int)
        logger.info("Metering reset for tenant %s period %s", tenant_id, key)
