"""Phase 3+ page e2e stub — Spec 029.

Skipped by default until LIVE_E2E=1 and stack/UI are healthy.
Does not invent green evidence for Ops Blueprint Phase 3 pages.
"""

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("LIVE_E2E", "0") != "1",
    reason="Spec 029 stub: set LIVE_E2E=1 when web + Kong healthy",
)


@pytest.mark.asyncio
async def test_phase3_agents_hub_stub(page, base_url):  # type: ignore[no-untyped-def]
    """Placeholder navigation check for Intelligence / agents surface."""
    await page.goto(f"{base_url}/")
    # Intentionally minimal — expand when LIVE_E2E campaigns resume.
    assert page.url.startswith(base_url)
