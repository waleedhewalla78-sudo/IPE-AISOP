"""Fernet password encryption for ERP connections (W1-04).

Uses IPE_ENCRYPTION_KEY. Generate with:
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

from __future__ import annotations

import os

from cryptography.fernet import Fernet

_key: bytes | None = None


def _get_key() -> bytes:
    global _key
    if not _key:
        raw = os.environ.get("IPE_ENCRYPTION_KEY", "")
        if not raw:
            raise ValueError("IPE_ENCRYPTION_KEY environment variable not set")
        _key = raw.encode() if isinstance(raw, str) else raw
    return _key


def reset_key_cache() -> None:
    """Test helper to clear cached key."""
    global _key
    _key = None


def encrypt_password(plaintext: str) -> str:
    return Fernet(_get_key()).encrypt(plaintext.encode()).decode()


def decrypt_password(ciphertext: str) -> str:
    return Fernet(_get_key()).decrypt(ciphertext.encode()).decode()
