"""Integration test configuration for Phases 3-5 strategy suite."""

from tests.integration.phases35_helpers import (  # noqa: F401
    REGISTRY,
    auth_headers,
    auth_token,
    client,
    fixtures_dir,
    registry,
    stack_available,
    write_report,
)


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    write_report(REGISTRY, REGISTRY.baseline_unit)
