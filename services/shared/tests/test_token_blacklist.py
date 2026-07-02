"""JWT blacklist tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from ipe_shared.auth.jwt import create_access_token, decode_token
from ipe_shared.auth.token_blacklist import blacklist_token, is_token_blacklisted


@pytest.mark.asyncio
async def test_blacklist_blocks_jti():
    jti = str(uuid4())
    exp = 2_000_000_000
    with patch("ipe_shared.auth.token_blacklist._get_client", new_callable=AsyncMock) as mock_client:
        redis = AsyncMock()
        redis.setex = AsyncMock()
        redis.exists = AsyncMock(return_value=1)
        mock_client.return_value = redis
        await blacklist_token(jti, exp)
        assert await is_token_blacklisted(jti) is True


@pytest.mark.asyncio
async def test_blacklist_noop_without_redis():
    assert await is_token_blacklisted("missing-jti") is False
