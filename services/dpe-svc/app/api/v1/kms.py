"""KMS API endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ipe_shared.kms.backend import get_kms

router = APIRouter(prefix="/kms", tags=["kms"])


class CreateKeyRequest(BaseModel):
    key_id: str = Field(..., min_length=1, max_length=128)
    algorithm: str = "AES-256"


class EncryptRequest(BaseModel):
    key_id: str
    plaintext: str


class DecryptRequest(BaseModel):
    key_id: str
    ciphertext: str


@router.post("/keys")
async def create_key(body: CreateKeyRequest) -> dict:
    kms = get_kms()
    key = kms.create_key(body.key_id, body.algorithm)
    return {"key_id": key.key_id, "key_arn": key.key_arn, "algorithm": key.algorithm}


@router.get("/keys")
async def list_keys() -> dict:
    kms = get_kms()
    keys = kms.list_keys()
    return {"keys": [{"key_id": k.key_id, "key_arn": k.key_arn} for k in keys]}


@router.post("/encrypt")
async def encrypt_data(body: EncryptRequest) -> dict:
    import base64
    kms = get_kms()
    ciphertext = kms.encrypt(body.key_id, body.plaintext.encode())
    return {"ciphertext": base64.b64encode(ciphertext).decode()}


@router.post("/decrypt")
async def decrypt_data(body: DecryptRequest) -> dict:
    import base64
    kms = get_kms()
    plaintext = kms.decrypt(body.key_id, base64.b64decode(body.ciphertext))
    return {"plaintext": plaintext.decode()}


@router.post("/keys/{key_id}/rotate")
async def rotate_key(key_id: str) -> dict:
    kms = get_kms()
    key = kms.rotate_key(key_id)
    return {"key_id": key.key_id, "rotated": True}
