"""Unit tests for lead time mapper pure helpers (no live Odoo)."""

from datetime import date

from app.odoo.mappers.lead_time_mapper import (
    compute_lead_time_days,
    compute_lead_time_variance_days,
)


def test_lead_time_days_normal():
    assert compute_lead_time_days(date(2026, 1, 1), date(2026, 1, 15)) == 14


def test_lead_time_variance_early_delivery():
    # Receipt before expected → negative variance
    assert compute_lead_time_variance_days(date(2026, 1, 20), date(2026, 1, 15)) == -5


def test_lead_time_missing_dates():
    assert compute_lead_time_days(None, date(2026, 1, 15)) is None
    assert compute_lead_time_days(date(2026, 1, 1), None) is None
    assert compute_lead_time_variance_days(None, date(2026, 1, 15)) is None
