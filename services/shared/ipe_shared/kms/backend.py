"""BYOK (Bring Your Own Key) KMS module for IPE.

Provides a pluggable KMS interface with AWS KMS and local (file-based) backends.
When AWS credentials are unavailable, uses local file-based key management.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("ipe.kms")


@dataclass
class KMSKey:
    key_id: str
    key_arn: str = ""
    algorithm: str = "AES-256"
    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()


class KMSBackend(ABC):
    @abstractmethod
    def create_key(self, key_id: str, algorithm: str = "AES-256") -> KMSKey: ...

    @abstractmethod
    def encrypt(self, key_id: str, plaintext: bytes) -> bytes: ...

    @abstractmethod
    def decrypt(self, key_id: str, ciphertext: bytes) -> bytes: ...

    @abstractmethod
    def rotate_key(self, key_id: str) -> KMSKey: ...

    @abstractmethod
    def list_keys(self) -> list[KMSKey]: ...


class LocalKMSBackend(KMSBackend):
    """File-based KMS for development/demo. NOT for production."""

    def __init__(self, key_dir: str = ".kms_keys") -> None:
        self._key_dir = Path(key_dir)
        self._key_dir.mkdir(parents=True, exist_ok=True)
        self._keys: dict[str, KMSKey] = {}
        self._load_keys()

    def _load_keys(self) -> None:
        for key_file in self._key_dir.glob("*.json"):
            data = json.loads(key_file.read_text())
            self._keys[data["key_id"]] = KMSKey(**data)

    def _save_key(self, key: KMSKey) -> None:
        key_file = self._key_dir / f"{key.key_id}.json"
        key_file.write_text(json.dumps({
            "key_id": key.key_id,
            "key_arn": key.key_arn,
            "algorithm": key.algorithm,
            "created_at": key.created_at,
            "metadata": key.metadata,
        }, indent=2))

    def create_key(self, key_id: str, algorithm: str = "AES-256") -> KMSKey:
        key_material = os.urandom(32)
        key = KMSKey(
            key_id=key_id,
            key_arn=f"local://{key_id}",
            algorithm=algorithm,
            metadata={"material_hash": hashlib.sha256(key_material).hexdigest()},
        )
        material_file = self._key_dir / f"{key_id}.key"
        material_file.write_bytes(key_material)
        self._keys[key_id] = key
        self._save_key(key)
        logger.info("KMS key created: %s (local backend)", key_id)
        return key

    def encrypt(self, key_id: str, plaintext: bytes) -> bytes:
        material_file = self._key_dir / f"{key_id}.key"
        if not material_file.exists():
            raise KeyError(f"Key not found: {key_id}")
        key_material = material_file.read_bytes()
        xor_ct = bytes(p ^ k for p, k in zip(plaintext, key_material * (len(plaintext) // len(key_material) + 1)))
        return base64.b64encode(xor_ct)

    def decrypt(self, key_id: str, ciphertext: bytes) -> bytes:
        material_file = self._key_dir / f"{key_id}.key"
        if not material_file.exists():
            raise KeyError(f"Key not found: {key_id}")
        key_material = material_file.read_bytes()
        decoded = base64.b64decode(ciphertext)
        return bytes(c ^ k for c, k in zip(decoded, key_material * (len(decoded) // len(key_material) + 1)))

    def rotate_key(self, key_id: str) -> KMSKey:
        old_key = self._keys.get(key_id)
        new_material = os.urandom(32)
        new_key = KMSKey(
            key_id=key_id,
            key_arn=old_key.key_arn if old_key else f"local://{key_id}",
            algorithm=old_key.algorithm if old_key else "AES-256",
            metadata={
                "rotated_at": datetime.now(UTC).isoformat(),
                "material_hash": hashlib.sha256(new_material).hexdigest(),
            },
        )
        material_file = self._key_dir / f"{key_id}.key"
        material_file.write_bytes(new_material)
        self._keys[key_id] = new_key
        self._save_key(new_key)
        logger.info("KMS key rotated: %s", key_id)
        return new_key

    def list_keys(self) -> list[KMSKey]:
        return list(self._keys.values())


class AWSKMSBackend(KMSBackend):
    """AWS KMS backend. Requires boto3 and valid credentials."""

    def __init__(self, region: str = "us-east-1") -> None:
        try:
            import boto3
            self._client = boto3.client("kms", region_name=region)
            logger.info("AWS KMS backend initialized (region=%s)", region)
        except Exception as exc:
            logger.warning("AWS KMS unavailable: %s — falling back to local", exc)
            raise

    def create_key(self, key_id: str, algorithm: str = "AES-256") -> KMSKey:
        resp = self._client.create_key(Description=f"IPE key: {key_id}")
        return KMSKey(
            key_id=key_id,
            key_arn=resp["KeyMetadata"]["Arn"],
            algorithm=algorithm,
        )

    def encrypt(self, key_id: str, plaintext: bytes) -> bytes:
        key_arn = self._get_key_arn(key_id)
        resp = self._client.encrypt(KeyId=key_arn, Plaintext=plaintext)
        return base64.b64encode(resp["CiphertextBlob"])

    def decrypt(self, key_id: str, ciphertext: bytes) -> bytes:
        resp = self._client.decrypt(CiphertextBlob=base64.b64decode(ciphertext))
        return resp["Plaintext"]

    def rotate_key(self, key_id: str) -> KMSKey:
        key_arn = self._get_key_arn(key_id)
        self._client.enable_key_rotation(KeyId=key_arn)
        return self.create_key(key_id)

    def list_keys(self) -> list[KMSKey]:
        resp = self._client.list_keys()
        return [KMSKey(key_id=k["KeyId"], key_arn=k["KeyArn"]) for k in resp["Keys"]]

    def _get_key_arn(self, key_id: str) -> str:
        resp = self._client.describe_key(KeyId=key_id)
        return resp["KeyMetadata"]["Arn"]


def get_kms_backend() -> KMSBackend:
    """Get KMS backend: AWS if configured, else local."""
    try:
        return AWSKMSBackend()
    except Exception:
        logger.info("Using local KMS backend for development")
        return LocalKMSBackend()


_kms_backend: KMSBackend | None = None


def get_kms() -> KMSBackend:
    global _kms_backend
    if _kms_backend is None:
        _kms_backend = get_kms_backend()
    return _kms_backend
