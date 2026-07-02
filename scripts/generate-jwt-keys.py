#!/usr/bin/env python3
"""Generate RS256 JWT key pair for IPE (cross-platform)."""

from __future__ import annotations

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ROOT = Path(__file__).resolve().parents[1]
KEY_DIR = ROOT / "config" / "keys"
PRIVATE_PATH = KEY_DIR / "jwt-private.pem"
PUBLIC_PATH = KEY_DIR / "jwt-public.pem"
EXAMPLE_PATH = KEY_DIR / "jwt-public.pem.example"


def main() -> None:
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    (KEY_DIR / "trusted").mkdir(exist_ok=True)

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    PRIVATE_PATH.write_bytes(private_pem)
    PUBLIC_PATH.write_bytes(public_pem)
    EXAMPLE_PATH.write_bytes(public_pem)

    print(f"Generated {PRIVATE_PATH}")
    print(f"Generated {PUBLIC_PATH}")
    print(f"Example public key: {EXAMPLE_PATH}")


if __name__ == "__main__":
    main()
