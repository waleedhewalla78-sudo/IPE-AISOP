"""Auto-confirm threshold tests (P8 R1-02)."""

from app.core.auto_confirm import should_auto_confirm
from ipe_shared.constants import AutonomyMode


class TestShouldAutoConfirm:
    def test_shadow_never_confirms(self):
        result = should_auto_confirm(0.99, AutonomyMode.SHADOW)
        assert result["should_confirm"] is False
        assert "Shadow" in result["reason"]

    def test_suggest_below_threshold(self):
        result = should_auto_confirm(0.80, AutonomyMode.SUGGEST)
        assert result["should_confirm"] is False

    def test_suggest_above_threshold(self):
        result = should_auto_confirm(0.90, AutonomyMode.SUGGEST, primary_constraint="capacity")
        assert result["should_confirm"] is True
        assert "capacity" in result["reason"]

    def test_autonomous_above_threshold(self):
        result = should_auto_confirm(0.75, AutonomyMode.AUTONOMOUS)
        assert result["should_confirm"] is True

    def test_unknown_mode_uses_high_threshold(self):
        result = should_auto_confirm(0.99, "unknown_mode")
        assert result["should_confirm"] is False
