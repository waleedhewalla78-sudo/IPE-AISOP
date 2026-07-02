"""Tests for audit hash chain publisher."""

import pytest

from ipe_shared.audit.kafka_publisher import _compute_hash


def test_hash_chain_links():
    first = {"action": "CREATE", "entity_id": "1"}
    h1 = _compute_hash(None, first)
    h2 = _compute_hash(h1, {"action": "UPDATE", "entity_id": "1"})
    assert h1 != h2
    assert len(h1) == 64
