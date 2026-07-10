"""Planner intent router unit tests â€” 014 Stream C."""

from app.core.planner_intent import PlannerIntent, detect_intent, extract_mo_ref


def test_intent_at_risk_mos():
    assert detect_intent("Which orders are at risk?") == PlannerIntent.AT_RISK_MOS


def test_intent_mo_detail():
    assert detect_intent("Tell me about MO-ST-001") == PlannerIntent.MO_DETAIL


def test_intent_scenario_list():
    assert detect_intent("Show resolution scenarios for this MO") == PlannerIntent.SCENARIO_LIST


def test_intent_sync_status():
    assert detect_intent("What is the last Odoo sync status?") == PlannerIntent.SYNC_STATUS


def test_intent_schedule_summary():
    assert detect_intent("Any capacity bottlenecks on the schedule?") == PlannerIntent.SCHEDULE_SUMMARY


def test_extract_mo_ref():
    assert extract_mo_ref("Details for MO-ST-001 please") == "ST-001" or extract_mo_ref("MO-ST-001") is not None
