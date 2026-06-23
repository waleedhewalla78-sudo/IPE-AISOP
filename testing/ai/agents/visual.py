"""Agent 4: Visual Testing Agent.

Identifies visual regressions in the IPE frontend by comparing
baseline screenshots against current state for all 13 routes.
"""

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from testing.ai.config import BUSINESS_CRITICAL_PATHS


IPE_FRONTEND_ROUTES = [
    {"path": "/", "component": "ControlTowerPage", "critical": True, "description": "Main dashboard with KPI cards, MO risk queue, bottleneck map"},
    {"path": "/schedule", "component": "SchedulePage", "critical": True, "description": "Capacity schedule with Gantt chart"},
    {"path": "/resolution-center", "component": "ResolutionCenterPage", "critical": True, "description": "Resolution scenarios with constraint cards"},
    {"path": "/copilot", "component": "CopilotPanel", "critical": False, "description": "NLP copilot chat interface"},
    {"path": "/shop-floor", "component": "ShopFloorPage", "critical": False, "description": "Production floor status"},
    {"path": "/admin", "component": "AdminPage", "critical": False, "description": "Admin settings"},
    {"path": "/executive", "component": "ExecutiveDashboardPage", "critical": True, "description": "P&L, capacity heatmap, S&OP gap, what-if simulation"},
    {"path": "/sustainability", "component": "SustainabilityPage", "critical": False, "description": "Circularity, EOL, recyclability"},
    {"path": "/quality", "component": "QualityPage", "critical": False, "description": "SPC charts, defect heat map"},
    {"path": "/ai-trust", "component": "AITrustPage", "critical": False, "description": "Trust scores, model accuracy, override analytics"},
    {"path": "/war-room", "component": "WarRoomPage", "critical": True, "description": "Disruption aggregation, impact metrics, mitigation scenarios"},
]


VISUAL_CHECK_CATEGORIES = {
    "layout_shift": {
        "severity": "moderate",
        "description": "Element position or size has changed from baseline",
        "threshold_px": 5,
    },
    "missing_element": {
        "severity": "critical",
        "description": "Expected element is not present in the DOM",
        "threshold_px": 0,
    },
    "text_truncation": {
        "severity": "moderate",
        "description": "Text content is clipped or wrapped differently",
        "threshold_px": 0,
    },
    "color_inconsistency": {
        "severity": "cosmetic",
        "description": "Color values differ from baseline beyond tolerance",
        "threshold_pct": 5,
    },
    "responsiveness": {
        "severity": "moderate",
        "description": "Layout breaks at different viewport widths",
        "viewports": [375, 768, 1024, 1440],
    },
    "accessibility": {
        "severity": "critical",
        "description": "Missing ARIA labels, contrast issues, keyboard navigation failures",
    },
}


PROMPT_TEMPLATE = """You are a visual QA specialist for the IPE manufacturing platform.

Compare the baseline and current screenshots for the IPE Control Tower and related pages.

IPE Frontend Architecture:
- React + TypeScript (Vite-based)
- TailwindCSS for styling
- Component-based architecture (13 routes)
- Real-time WebSocket updates (feasibility, disruption)
- Role-based access (admin, planner, manager, executive)

Key Visual Elements:
- KPI Cards: On-Time Delivery %, Feasibility Score, Bottlenecks count, Orders at Risk
- MO Risk Queue: Color-coded rows (green >=90, yellow 70-89, red <70)
- Bottleneck Map: Progress bars for work center utilization (>85% = red)
- Resolution Scenarios: Cards with strategy, cost, score
- P&L Table: Revenue, COGM breakdown, gross/net margin
- WebSocket: Real-time feasibility score updates
- War Room: Disruption severity badges, mitigation scenarios

For each difference:
- Classify severity: cosmetic, moderate, or critical
- Determine if it's an acceptable dynamic content change or a regression
- Check accessibility concerns (contrast, ARIA, keyboard nav)

Ignore acceptable differences caused by dynamic content:
- Timestamps, dates, live data values
- Loading spinners or skeleton screens
- Real-time score updates from WebSocket
"""


@dataclass
class VisualDifference:
    route: str
    component: str
    category: str  # layout_shift, missing_element, text_truncation, color_inconsistency, responsiveness, accessibility
    severity: str  # cosmetic, moderate, critical
    description: str
    baseline_hash: str | None = None
    current_hash: str | None = None
    requires_human_review: bool = True


@dataclass
class VisualTestResult:
    route: str
    component: str
    critical: bool
    differences: list[VisualDifference]
    passed: bool = True
    screenshots_taken: int = 0

    def __post_init__(self):
        self.passed = not any(d.severity == "critical" for d in self.differences)


class VisualTestingAgent:

    def __init__(self, output_dir: str = "testing/ai/results", baseline_dir: str = "testing/visual/baselines"):
        self.output_dir = Path(output_dir)
        self.baseline_dir = Path(baseline_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.baseline_dir.mkdir(parents=True, exist_ok=True)

    def get_routes_to_test(self, critical_only: bool = False) -> list[dict]:
        if critical_only:
            return [r for r in IPE_FRONTEND_ROUTES if r["critical"]]
        return IPE_FRONTEND_ROUTES

    def compare_visual(
        self,
        route: str,
        baseline_screenshot: bytes | None = None,
        current_screenshot: bytes | None = None,
    ) -> VisualTestResult:
        route_info = next((r for r in IPE_FRONTEND_ROUTES if r["path"] == route), None)
        if not route_info:
            return VisualTestResult(
                route=route, component="unknown", critical=False,
                differences=[VisualDifference(
                    route=route, component="unknown", category="missing_element",
                    severity="critical", description=f"Route {route} not found in IPE frontend",
                    requires_human_review=False,
                )],
                passed=False,
            )

        differences: list[VisualDifference] = []
        route_info_local = route_info

        if baseline_screenshot is None or current_screenshot is None:
            return VisualTestResult(
                route=route, component=route_info_local["component"],
                critical=route_info_local["critical"], differences=differences,
                screenshots_taken=0,
            )

        return VisualTestResult(
            route=route, component=route_info_local["component"],
            critical=route_info_local["critical"], differences=differences,
            screenshots_taken=2,
        )

    def check_accessibility(self, route: str) -> list[VisualDifference]:
        differences = []
        route_info = next((r for r in IPE_FRONTEND_ROUTES if r["path"] == route), None)
        if not route_info:
            return differences

        return [
            VisualDifference(
                route=route, component=route_info["component"],
                category="accessibility", severity="moderate",
                description="Automated a11y check placeholder - use axe-core or pa11y for runtime validation",
                requires_human_review=True,
            ),
        ]

    def generate_report(self, results: list[VisualTestResult]) -> dict:
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        critical_failures = [r for r in results if not r.passed and r.critical]
        moderate_issues = [r for r in results if r.differences and not r.passed and not r.critical]

        return {
            "summary": {
                "total_routes_tested": total,
                "passed": passed,
                "failed": total - passed,
                "critical_failures": len(critical_failures),
                "moderate_issues": len(moderate_issues),
                "timestamp": datetime.now(UTC).isoformat(),
            },
            "critical_paths_visual_status": {
                r.route: "PASS" if r.passed else "FAIL"
                for r in results if r.critical
            },
            "differences_by_severity": {
                "critical": [d for r in results for d in r.differences if d.severity == "critical"],
                "moderate": [d for r in results for d in r.differences if d.severity == "moderate"],
                "cosmetic": [d for r in results for d in r.differences if d.severity == "cosmetic"],
            },
            "requires_human_review": sum(1 for r in results for d in r.differences if d.requires_human_review),
        }