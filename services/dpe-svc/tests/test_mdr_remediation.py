"""MDR remediation + routing deviation — R2-05."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.mdr_engine import build_remediation, detect_routing_deviation


def test_build_remediation_all_gaps():
    steps = build_remediation(
        {
            "composite_score": 50.0,
            "bom_completeness_pct": 70.0,
            "lead_time_accuracy_pct": 50.0,
            "routing_accuracy_pct": 60.0,
            "inventory_accuracy_pct": 50.0,
        }
    )
    assert len(steps) == 5
    assert any("Composite MDR" in s for s in steps)
    assert any("BOM" in s for s in steps)


def test_build_remediation_passing():
    assert build_remediation(
        {
            "composite_score": 85.0,
            "bom_completeness_pct": 90.0,
            "lead_time_accuracy_pct": 80.0,
            "routing_accuracy_pct": 90.0,
            "inventory_accuracy_pct": 90.0,
        }
    ) == []


@pytest.mark.asyncio
async def test_detect_routing_deviation_no_tenant():
    session = AsyncMock()
    assert await detect_routing_deviation(session, tenant_id=None) == []


@pytest.mark.asyncio
async def test_detect_routing_deviation_flags_large_deviation():
    tid = str(uuid4())
    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(),
            MagicMock(
                fetchall=MagicMock(
                    return_value=[
                        (uuid4(), uuid4(), 100.0, 150.0, uuid4()),
                        (uuid4(), uuid4(), 100.0, 105.0, None),
                    ]
                )
            ),
        ]
    )
    drafts = await detect_routing_deviation(session, tenant_id=tid, threshold_pct=10.0)
    assert len(drafts) == 1
    assert drafts[0]["deviation_pct"] == 50.0
    assert drafts[0]["status"] == "pending_approval"
