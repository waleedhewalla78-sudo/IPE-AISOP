import pytest

from app.core.contextual_intelligence import ContextualIntelligence, MeetingPreparator


@pytest.mark.asyncio
async def test_morning_brief():
    intel = ContextualIntelligence()
    brief = await intel.generate_morning_brief(
        "tenant-1",
        "Ahmed",
        {
            "exceptions": [{"severity": "high", "title": "Stockout risk", "entity_type": "mo"}],
            "predictions": [{"trend": "crisis_approaching", "recommended_action": "Act now"}],
            "otd": {"current_pct": 89, "trend_direction": "stable", "total_mos": 47},
        },
    )
    assert "Ahmed" in brief["greeting"]
    assert brief["urgent"]
    assert brief["otd_current"] == 89


def test_meeting_prep_templates():
    prep = MeetingPreparator()
    brief = prep.prepare("production_meeting")
    assert "yesterday_performance" in brief["sections"]
    assert "A3" in brief["data_sources"]
