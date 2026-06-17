import pytest
from ipe_shared.constants import (
    DemandType, MOStatus, AutonomyMode, DelayCategory, TenantTier
)


class TestConstants:
    def test_demand_type_values(self):
        assert DemandType.MAKE_TO_ORDER.value == "MTO"
        assert DemandType.MAKE_TO_STOCK.value == "MTS"

    def test_mo_status_values(self):
        assert MOStatus.DRAFT.value == "draft"
        assert MOStatus.CONFIRMED.value == "confirmed"

    def test_autonomy_mode_values(self):
        assert AutonomyMode.SHADOW.value == "shadow"
        assert AutonomyMode.AUTONOMOUS.value == "autonomous"

    def test_delay_category_count(self):
        assert len(DelayCategory) == 8

    def test_tenant_tier_values(self):
        assert TenantTier.PROFESSIONAL.value == "professional"
