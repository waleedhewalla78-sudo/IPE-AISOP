#!/usr/bin/env python3
"""Generate self-signed TLS certificates for IPE dev (Kong :8443)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CERT_DIR = ROOT / "infrastructure" / "certs"
KEY = CERT_DIR / "ipe-dev.key"
CRT = CERT_DIR / "ipe-dev.crt"


def _openssl() -> bool:
    CERT_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        "openssl", "req", "-x509", "-nodes", "-days", "365", "-newkey", "rsa:2048",
        "-keyout", str(KEY), "-out", str(CRT),
        "-subj", "/CN=localhost/O=IPE/C=US",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def _cryptography() -> None:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    import datetime

    CERT_DIR.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "IPE"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.UTC))
        .not_valid_after(datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
        .sign(key, hashes.SHA256())
    )
    KEY.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    CRT.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def main() -> int:
    if not _openssl():
        _cryptography()
    KEY.chmod(0o600)
    CRT.chmod(0o644)
    print(f"TLS certs ready: {CRT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
