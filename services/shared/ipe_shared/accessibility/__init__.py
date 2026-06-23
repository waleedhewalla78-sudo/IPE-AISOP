"""IPE Accessibility module — WCAG 2.1 AA testing utilities."""
from ipe_shared.accessibility.wcag import (
    AccessibilityViolation,
    AccessibilityReport,
    WCAG_2_1_AA_RULES,
    IPE_ACCESSIBILITY_REQUIREMENTS,
    IPE_ROUTE_ACCESSIBILITY,
    generate_accessibility_test_config,
    validate_ipe_accessibility,
)

__all__ = [
    "AccessibilityViolation", "AccessibilityReport",
    "WCAG_2_1_AA_RULES", "IPE_ACCESSIBILITY_REQUIREMENTS",
    "IPE_ROUTE_ACCESSIBILITY",
    "generate_accessibility_test_config", "validate_ipe_accessibility",
]
