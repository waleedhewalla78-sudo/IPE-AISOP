import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def kms_key_dir(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("IPE_KMS_KEY_DIR", tmp)
        # Reset cached KMS singleton between tests
        import ipe_shared.kms.backend as kms_mod

        kms_mod._kms_backend = None
        yield Path(tmp)
        kms_mod._kms_backend = None


def test_encrypt_decrypt_roundtrip(kms_key_dir):
    from ipe_shared.integrations.odoo_credentials import (
        decrypt_odoo_password,
        encrypt_odoo_password,
        odoo_password_is_set,
        store_odoo_password,
    )

    enc = encrypt_odoo_password("secret-pass")
    assert enc
    cfg = {"odoo_password_enc": enc}
    assert decrypt_odoo_password(cfg) == "secret-pass"
    assert odoo_password_is_set(cfg)

    updated = store_odoo_password({"odoo_password": "legacy"}, "new-secret")
    assert "odoo_password" not in updated
    assert decrypt_odoo_password(updated) == "new-secret"


def test_legacy_plaintext_fallback(kms_key_dir):
    from ipe_shared.integrations.odoo_credentials import decrypt_odoo_password, odoo_password_is_set

    cfg = {"odoo_password": "plain"}
    assert decrypt_odoo_password(cfg) == "plain"
    assert odoo_password_is_set(cfg)


def test_missing_password_returns_none(kms_key_dir):
    from ipe_shared.integrations.odoo_credentials import decrypt_odoo_password, odoo_password_is_set

    assert decrypt_odoo_password({}) is None
    assert not odoo_password_is_set({})
