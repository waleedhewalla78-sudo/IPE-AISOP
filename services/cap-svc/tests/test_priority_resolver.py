"""Tests for MO priority resolution."""

from app.core.priority_resolver import normalize_priority


def test_normalize_priority_from_percent():
    assert normalize_priority(92) == 0.92


def test_normalize_priority_from_fraction():
    assert normalize_priority(0.75) == 0.75


def test_normalize_priority_floor():
    assert normalize_priority(0) == 0.01
