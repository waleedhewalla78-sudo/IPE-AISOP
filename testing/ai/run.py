"""IPE AI-Augmented Testing Framework — CLI Runner.

Usage:
    python -m testing.ai.run [command] [options]

Commands:
    generate    — Run Test Generation Agent
    regression  — Run Regression Testing Agent
    heal        — Run Self-Healing Agent
    visual      — Run Visual Testing Agent
    explore    — Run Exploratory Testing Agent
    optimize    — Run Test Optimization Agent
    all         — Run all agents and produce combined report
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from testing.ai.agents.generator import TestGenerationAgent
from testing.ai.agents.regression import RegressionAgent
from testing.ai.agents.self_healing import SelfHealingAgent
from testing.ai.agents.visual import VisualTestingAgent
from testing.ai.agents.exploratory import ExploratoryTestingAgent
from testing.ai.agents.optimizer import TestOptimizationAgent
from testing.ai.config import SERVICE_REGISTRY


def run_generate(args):
    agent = TestGenerationAgent(output_dir=args.output)
    result = agent.generate_from_requirements(
        requirements=args.requirements or "IPE platform - all services, all endpoints",
    )
    rls_tests = agent.generate_rls_tests()
    xai_tests = agent.generate_xai_tests()
    result.test_cases.extend(rls_tests)
    result.test_cases.extend(xai_tests)
    path = agent.export_to_json(result)

    print(f"\n=== Test Generation Agent ===")
    print(f"Total test cases generated: {result.total_count}")
    print(f"  By category: {result.by_category}")
    print(f"  By service: {result.by_service}")
    print(f"  RLS isolation tests: {len(rls_tests)}")
    print(f"  XAI compliance tests: {len(xai_tests)}")
    print(f"  Coverage gaps: {result.coverage_gaps}")
    print(f"  Suggestions: {result.suggestions}")
    print(f"\nOutput: {path}")
    return result


def run_regression(args):
    agent = RegressionAgent(output_dir=args.output)
    changed = args.services.split(",") if args.services else list(SERVICE_REGISTRY.keys())
    suite = agent.prioritize(
        changed_services=changed,
        defect_history=json.loads(args.defects) if args.defects else {},
        release_scope=args.scope,
    )
    path = agent.export_to_json(suite)

    print(f"\n=== Regression Testing Agent ===")
    print(f"Suite ID: {suite.suite_id}")
    print(f"  Must run: {len(suite.must_run)} tests")
    print(f"  Should run: {len(suite.should_run)} tests")
    print(f"  Optional: {len(suite.optional)} tests")
    print(f"  Estimated time: {suite.total_estimated_time_seconds}s")
    print(f"  Critical path coverage: {suite.critical_path_coverage}")
    print(f"\nOutput: {path}")
    return suite


def run_heal(args):
    agent = SelfHealingAgent(output_dir=args.output)
    result = agent.analyze_failure(
        test_file=args.test_file or "unknown",
        service=args.service or "unknown",
        error_log=args.error_log or "",
        response_diff=json.loads(args.response_diff) if args.response_diff else None,
    )

    print(f"\n=== Self-Healing Agent ===")
    print(f"Total fixes: {len(result.fixes)}")
    print(f"  Auto-applicable: {result.auto_applicable}")
    print(f"  Requires review: {result.requires_review}")
    for fix in result.fixes:
        print(f"  - {fix.root_cause}: {fix.proposed} (confidence: {fix.confidence})")
    print(f"\nSummary: {result.summary}")
    return result


def run_visual(args):
    agent = VisualTestingAgent(output_dir=args.output)
    routes = agent.get_routes_to_test(critical_only=args.critical_only)
    results = []
    for route in routes:
        result = agent.compare_visual(route=route["path"])
        results.append(result)

    report = agent.generate_report(results)
    print(f"\n=== Visual Testing Agent ===")
    print(f"Routes tested: {report['summary']['total_routes_tested']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Critical failures: {report['summary']['critical_failures']}")
    print(f"Requires human review: {report['requires_human_review']}")
    return report


def run_explore(args):
    agent = ExploratoryTestingAgent(output_dir=args.output)
    session = agent.generate_charters(
        focus_areas=args.areas.split(",") if args.areas else None,
    )
    path = agent.export_to_json(session)

    print(f"\n=== Exploratory Testing Agent ===")
    print(f"Session ID: {session.session_id}")
    print(f"Total charters: {len(session.charters)}")
    print(f"Critical path charters: {session.critical_path_charters}")
    print(f"Total test ideas: {session.total_ideas}")
    for charter in session.charters[:5]:
        print(f"  [{charter.risk_level.value}] {charter.target_area}: {charter.mission[:80]}...")
    if len(session.charters) > 5:
        print(f"  ... and {len(session.charters) - 5} more charters")
    print(f"\nOutput: {path}")
    return session


def run_optimize(args):
    agent = TestOptimizationAgent(output_dir=args.output)
    result = agent.analyze(
        changed_services=args.services.split(",") if args.services else None,
    )
    path = agent.export_to_json(result)

    print(f"\n=== Test Optimization Agent ===")
    print(f"Total tests analyzed: {result.total_tests}")
    print(f"  Keep: {result.keep}")
    print(f"  Remove: {result.remove}")
    print(f"  Merge: {result.merge}")
    print(f"  Skip for PR: {result.skip_for_pr}")
    print(f"  PR build estimate: {result.pr_build_time_estimate_seconds}s")
    print(f"  Full build estimate: {result.full_build_time_estimate_seconds}s")
    print(f"  Nightly build estimate: {result.nightly_build_time_estimate_seconds}s")
    print(f"  Coverage gaps: {len(result.coverage_gaps)}")
    for gap in result.coverage_gaps[:5]:
        print(f"    - {gap}")
    print(f"\nOutput: {path}")
    return result


def run_all(args):
    print("=" * 60)
    print("IPE AI-Augmented Testing Framework — Full Run")
    print("=" * 60)
    print(f"Timestamp: {datetime.now(UTC).isoformat()}\n")

    gen_result = run_generate(args)
    reg_result = run_regression(args)
    vis_result = run_visual(args)
    exp_result = run_explore(args)
    opt_result = run_optimize(args)

    combined = {
        "timestamp": datetime.now(UTC).isoformat(),
        "generated_tests": gen_result.total_count,
        "regression_must_run": len(reg_result.must_run),
        "visual_passed": vis_result["summary"]["passed"],
        "exploratory_charters": len(exp_result.charters),
        "optimization_keep": opt_result.keep,
        "coverage_gaps": opt_result.coverage_gaps,
    }
    combined_path = Path(args.output) / "combined_report.json"
    combined_path.parent.mkdir(parents=True, exist_ok=True)
    combined_path.write_text(json.dumps(combined, indent=2))

    print(f"\n{'=' * 60}")
    print(f"Combined report: {combined_path}")
    print(f"{'=' * 60}")
    return combined


def main():
    parser = argparse.ArgumentParser(description="IPE AI-Augmented Testing Framework")
    parser.add_argument("--output", default="testing/ai/results", help="Output directory for results")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    gen = subparsers.add_parser("generate", help="Generate test cases from requirements")
    gen.add_argument("--requirements", default="", help="Requirements text or file path")

    reg = subparsers.add_parser("regression", help="Prioritize regression suite")
    reg.add_argument("--services", default="", help="Comma-separated changed services")
    reg.add_argument("--defects", default="{}", help="JSON defect history")
    reg.add_argument("--scope", default="patch", choices=["patch", "minor", "major"])

    heal = subparsers.add_parser("heal", help="Analyze test failures and suggest fixes")
    heal.add_argument("--test-file", default="", help="Failed test file")
    heal.add_argument("--service", default="", help="Service name")
    heal.add_argument("--error-log", default="", help="Error log text")
    heal.add_argument("--response-diff", default="", help="JSON response diff")

    vis = subparsers.add_parser("visual", help="Visual regression testing")
    vis.add_argument("--critical-only", action="store_true", help="Only test critical routes")

    exp = subparsers.add_parser("explore", help="Generate exploratory test charters")
    exp.add_argument("--areas", default="", help="Comma-separated focus areas")

    opt = subparsers.add_parser("optimize", help="Optimize test suite")
    opt.add_argument("--services", default="", help="Comma-separated changed services")

    subparsers.add_parser("all", help="Run all agents")

    args = parser.parse_args()

    if args.command == "generate":
        run_generate(args)
    elif args.command == "regression":
        run_regression(args)
    elif args.command == "heal":
        run_heal(args)
    elif args.command == "visual":
        run_visual(args)
    elif args.command == "explore":
        run_explore(args)
    elif args.command == "optimize":
        run_optimize(args)
    elif args.command == "all":
        run_all(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()