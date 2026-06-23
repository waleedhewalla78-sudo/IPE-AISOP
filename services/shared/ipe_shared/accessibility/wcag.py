"""WCAG 2.1 AA accessibility testing utilities for IPE frontend.

Provides automated accessibility checks using axe-core patterns.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AccessibilityViolation:
    rule_id: str
    description: str
    impact: str  # critical, serious, moderate, minor
    target: str  # CSS selector
    help_url: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class AccessibilityReport:
    url: str = ""
    violations: list[AccessibilityViolation] = field(default_factory=list)
    passes: int = 0
    incomplete: int = 0
    inapplicable: int = 0
    timestamp: str = ""

    @property
    def is_compliant(self) -> bool:
        critical = sum(1 for v in self.violations if v.impact == "critical")
        serious = sum(1 for v in self.violations if v.impact == "serious")
        return critical == 0 and serious == 0

    @property
    def violation_summary(self) -> dict[str, int]:
        summary: dict[str, int] = {}
        for v in self.violations:
            summary[v.impact] = summary.get(v.impact, 0) + 1
        return summary


# WCAG 2.1 AA critical rules for manufacturing/enterprise apps
WCAG_2_1_AA_RULES: list[dict[str, Any]] = [
    {"rule_id": "color-contrast", "description": "Elements must have sufficient color contrast ratio (≥4.5:1)", "impact": "serious", "tags": ["cat.color", "wcag2a", "wcag143"]},
    {"rule_id": "label", "description": "Form elements must have labels", "impact": "critical", "tags": ["cat.forms", "wcag2a", "wcag412"]},
    {"rule_id": "image-alt", "description": "Images must have alternate text", "impact": "critical", "tags": ["cat.text-alternatives", "wcag2a", "wcag111"]},
    {"rule_id": "link-name", "description": "Links must have discernible text", "impact": "serious", "tags": ["cat.name-role-value", "wcag2a", "wcag244"]},
    {"rule_id": "button-name", "description": "Buttons must have discernible text", "impact": "critical", "tags": ["cat.name-role-value", "wcag2a", "wcag412"]},
    {"rule_id": "html-has-lang", "description": "html element must have a lang attribute", "impact": "serious", "tags": ["cat.language", "wcag2a", "wcag311"]},
    {"rule_id": "document-title", "description": "Documents must have a title", "impact": "serious", "tags": ["cat.structure", "wcag2a", "wcag242"]},
    {"rule_id": "duplicate-id", "description": "IDs must be unique", "impact": "moderate", "tags": ["cat.parsing", "wcag2a", "wcag411"]},
    {"rule_id": "heading-order", "description": "Heading levels should increase by one", "impact": "moderate", "tags": ["cat.semantics", "wcag2a", "wcag131"]},
    {"rule_id": "region", "description": "All page content should be contained by landmarks", "impact": "moderate", "tags": ["cat.structure", "wcag2a", "wcag131"]},
    {"rule_id": "aria-required-attr", "description": "Required ARIA attributes must be provided", "impact": "critical", "tags": ["cat.forms", "wcag2a", "wcag412"]},
    {"rule_id": "aria-valid-attr-value", "description": "ARIA attributes must have valid values", "impact": "critical", "tags": ["cat.forms", "wcag2a", "wcag412"]},
    {"rule_id": "aria-valid-attr", "description": "ARIA attributes must be valid", "impact": "serious", "tags": ["cat.forms", "wcag2a", "wcag412"]},
    {"rule_id": "tabindex", "description": "tabindex attributes should not be greater than 0", "impact": "serious", "tags": ["cat.name-role-value", "wcag2a", "wcag242"]},
    {"rule_id": "bypass", "description": "Page should have means to bypass repeated blocks", "impact": "serious", "tags": ["cat.structure", "wcag2a", "wcag241"]},
    {"rule_id": "scrollable-region-focusable", "description": "Scrollable region must be keyboard accessible", "impact": "serious", "tags": ["cat.keyboard", "wcag2a", "wcag211"]},
]

# IPE-specific accessibility requirements
IPE_ACCESSIBILITY_REQUIREMENTS: list[dict[str, Any]] = [
    {"requirement": "Keyboard navigation", "description": "All interactive elements accessible via Tab/Enter/Space", "critical": True},
    {"requirement": "Screen reader support", "description": "All data tables have proper th/scope/caption", "critical": True},
    {"requirement": "Focus management", "description": "Focus visible on all interactive elements (2px solid outline)", "critical": True},
    {"requirement": "Color independence", "description": "Information conveyed by color also has text/icon alternative", "critical": True},
    {"requirement": "Motion reduction", "description": "Respect prefers-reduced-motion media query", "critical": False},
    {"requirement": "Text resize", "description": "Content readable at 200% zoom without horizontal scroll", "critical": True},
    {"requirement": "Error identification", "description": "Form errors identified in text, not just color", "critical": True},
    {"requirement": "Language identification", "description": "Page language set via html lang attribute", "critical": True},
    {"requirement": "Consistent navigation", "description": "Navigation order consistent across pages", "critical": False},
    {"requirement": "Touch targets", "description": "Interactive targets ≥44x44 CSS pixels", "critical": False},
]


def generate_accessibility_test_config() -> dict[str, Any]:
    """Generate axe-core configuration for IPE accessibility testing."""
    return {
        "rules": {rule["rule_id"]: {"enabled": True} for rule in WCAG_2_1_AA_RULES},
        "reporter": "v2",
        "checks": [],
        "tags": ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "best-practice"],
        "resultTypes": ["violations", "passes", "incomplete", "inapplicable"],
    }


def validate_ipe_accessibility() -> dict[str, Any]:
    """Validate IPE-specific accessibility requirements."""
    results = []
    for req in IPE_ACCESSIBILITY_REQUIREMENTS:
        results.append({
            "requirement": req["requirement"],
            "description": req["description"],
            "critical": req["critical"],
            "status": "needs_manual_verification",
        })

    return {
        "total_requirements": len(IPE_ACCESSIBILITY_REQUIREMENTS),
        "critical_requirements": sum(1 for r in IPE_ACCESSIBILITY_REQUIREMENTS if r["critical"]),
        "results": results,
        "note": "Automated checks cover ~30% of WCAG 2.1 AA. Manual audit recommended for full compliance.",
    }


# Frontend route accessibility mapping
IPE_ROUTE_ACCESSIBILITY: dict[str, dict[str, Any]] = {
    "/control-tower": {
        "page": "Control Tower Dashboard",
        "critical_elements": ["KPI cards", "MO Risk Queue table", "Bottleneck map"],
        "keyboard_requirements": ["Tab through KPI cards", "Enter to resolve MO", "Arrow keys for table"],
        "screen_reader_requirements": ["Table headers with scope", "KPI values with labels", "Status announcements"],
    },
    "/schedule": {
        "page": "Schedule View",
        "critical_elements": ["Gantt chart", "MO list", "Filter controls"],
        "keyboard_requirements": ["Tab to filters", "Enter to select MO", "Escape to close modals"],
        "screen_reader_requirements": ["Schedule summary", "MO status announcements", "Filter state"],
    },
    "/resolution": {
        "page": "Resolution Center",
        "critical_elements": ["MO constraint list", "Scenario comparison cards", "Approve/reject buttons"],
        "keyboard_requirements": ["Tab through scenarios", "Enter to approve", "Space to reject"],
        "screen_reader_requirements": ["Constraint details", "Scenario recommendations", "Action confirmations"],
    },
    "/shop-floor": {
        "page": "Shop Floor PWA",
        "critical_elements": ["Barcode scanner input", "MO progress cards", "Online/offline status"],
        "keyboard_requirements": ["Tab to scanner", "Enter to submit scan", "Arrow keys for MO list"],
        "screen_reader_requirements": ["Scan results", "Progress updates", "Sync status"],
    },
    "/executive": {
        "page": "Executive Dashboard",
        "critical_elements": ["P&L table", "S&OP gap analysis", "What-if simulation"],
        "keyboard_requirements": ["Tab to controls", "Enter to simulate", "Arrow keys for table"],
        "screen_reader_requirements": ["Financial summaries", "Gap descriptions", "Simulation results"],
    },
}
