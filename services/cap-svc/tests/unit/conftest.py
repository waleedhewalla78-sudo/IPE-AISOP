"""Override service conftest DB for lightweight unit tests."""

import pytest


@pytest.fixture(autouse=True)
async def db():
    yield
