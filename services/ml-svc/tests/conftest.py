import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("IPE_JWT_SECRET_KEY", "dev-jwt-secret-change-in-production-min-32-chars")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

import pytest

from ipe_shared.testing.conftest_helpers import (
    apply_auth_and_session_overrides,
    clear_overrides,
)


@pytest.fixture
def client():
    from app.main import create_app
    from fastapi.testclient import TestClient

    app = create_app()
    apply_auth_and_session_overrides(app)
    with TestClient(app) as c:
        yield c
    clear_overrides(app)
