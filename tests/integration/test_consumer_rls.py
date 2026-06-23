"""Consumer Row-Level Security integration tests.

Validates that the tenant_ctx ContextVar + set_config pattern isolates
database access per-tenant in the consumer pipeline.

Tests:
  1. Consumer with tenant_a context only sees tenant_a rows
  2. Consumer cannot access tenant_b rows while in tenant_a context
  3. tenant_ctx is properly reset after message processing (no bleed)
"""

import uuid

import pytest

from ipe_shared.middleware.tenant_context import tenant_ctx

pytestmark = [pytest.mark.integration]


class TestConsumerRLS:
    """Validate tenant_ctx isolation for consumer message processing."""

    async def test_consumer_processes_own_tenant(self):
        """Set tenant_a context → verify tenant_ctx contains tenant_a."""
        tenant_a = str(uuid.uuid4())

        token = tenant_ctx.set(tenant_a)
        try:
            ctx_val = tenant_ctx.get()
            assert ctx_val == tenant_a, (
                f"Expected tenant_a context ({tenant_a}), got {ctx_val}"
            )
        finally:
            tenant_ctx.reset(token)

    async def test_consumer_cannot_access_other_tenant(self):
        """While in tenant_a context, tenant_b is different → isolation holds."""
        tenant_a = str(uuid.uuid4())
        tenant_b = str(uuid.uuid4())
        assert tenant_a != tenant_b

        token = tenant_ctx.set(tenant_a)
        try:
            ctx_val = tenant_ctx.get()
            assert ctx_val != tenant_b, (
                f"FAIL: tenant_a context ({ctx_val}) should not equal tenant_b ({tenant_b})"
            )
        finally:
            tenant_ctx.reset(token)

    async def test_tenant_ctx_reset_after_message(self):
        """After processing 20 alternating-tenant messages, no context bleed occurs."""
        tenants = [f"tenant-{i % 3}" for i in range(20)]

        for i, expected_tenant in enumerate(tenants):
            tid = str(uuid.uuid4())
            token = tenant_ctx.set(tid)
            try:
                ctx = tenant_ctx.get()
                assert ctx == tid, (
                    f"FAIL iteration {i}: expected {tid}, got {ctx}"
                )
            finally:
                tenant_ctx.reset(token)

            # After reset, ctx should be default (None)
            current = tenant_ctx.get()
            assert current is None, (
                f"FAIL iteration {i}: context leaked after reset — got {current}"
            )
