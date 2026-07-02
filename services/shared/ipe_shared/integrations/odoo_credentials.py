"""Encrypted Odoo credential storage (T081).

Passwords are stored as KMS-encrypted `odoo_password_enc` in tenant JSONB config.
Legacy plaintext `odoo_password` is still read for migration but removed on update.
"""

from __future__ import annotations

import base64
import logging
import os

from ipe_shared.kms import get_kms

logger = logging.getLogger(__name__)

ODOO_KMS_KEY_ID = "ipe-odoo-credentials"
ENC_FIELD = "odoo_password_enc"
LEGACY_FIELD = "odoo_password"


def _ensure_kms_key() -> None:
    kms = get_kms()
    if ODOO_KMS_KEY_ID not in {k.key_id for k in kms.list_keys()}:
        kms.create_key(ODOO_KMS_KEY_ID)
        logger.info("Created KMS key for Odoo credentials: %s", ODOO_KMS_KEY_ID)


def encrypt_odoo_password(plaintext: str) -> str:
    _ensure_kms_key()
    ciphertext = get_kms().encrypt(ODOO_KMS_KEY_ID, plaintext.encode("utf-8"))
    return base64.b64encode(ciphertext).decode("ascii")


def decrypt_odoo_password(cfg: dict) -> str | None:
    enc = cfg.get(ENC_FIELD)
    if enc:
        try:
            raw = base64.b64decode(enc.encode("ascii"))
            return get_kms().decrypt(ODOO_KMS_KEY_ID, raw).decode("utf-8")
        except Exception:
            logger.exception("Failed to decrypt Odoo password for tenant config")
            return None
    legacy = cfg.get(LEGACY_FIELD)
    if legacy:
        return str(legacy)
    return None


def odoo_password_is_set(cfg: dict) -> bool:
    return bool(cfg.get(ENC_FIELD) or cfg.get(LEGACY_FIELD))


def store_odoo_password(cfg: dict, password: str) -> dict:
    """Encrypt password and strip legacy plaintext from config copy."""
    updated = dict(cfg)
    updated[ENC_FIELD] = encrypt_odoo_password(password)
    updated.pop(LEGACY_FIELD, None)
    return updated
