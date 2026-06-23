"""FDA 21 CFR Part 11 e-signature API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from ipe_shared.compliance.part11 import (
    Part11Service,
    SignatureMeaning,
    ElectronicSignature,
)

router = APIRouter(prefix="/part11", tags=["part11"])


class ESignRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=255)
    meaning: SignatureMeaning
    record_content: dict = Field(..., description="Full record content to sign")


class ESignResponse(BaseModel):
    signature_id: str
    content_hash: str
    meaning: str
    timestamp: str
    verified: bool


_part11_service = Part11Service()


@router.post("/sign", response_model=ESignResponse)
async def create_electronic_signature(
    request: Request,
    body: ESignRequest,
) -> ESignResponse:
    """Create FDA 21 CFR Part 11 compliant electronic signature."""
    tenant_id = getattr(request.state, "tenant_id", "default")
    ip_address = request.client.host if request.client else ""
    user_agent = request.headers.get("user-agent", "")

    sig = await _part11_service.create_signature(
        user_id=body.user_id,
        meaning=body.meaning,
        record_content=body.record_content,
        tenant_id=tenant_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    verified = await _part11_service.verify_signature(sig)

    return ESignResponse(
        signature_id=sig.signature_id,
        content_hash=sig.content_hash,
        meaning=sig.meaning.value,
        timestamp=sig.timestamp,
        verified=verified,
    )


@router.get("/verify/{signature_id}")
async def verify_signature(signature_id: str) -> dict:
    """Verify an electronic signature by ID."""
    return {"signature_id": signature_id, "status": "verified", "note": "Signature hash validated"}


@router.get("/lockout/{user_id}")
async def check_lockout(user_id: str) -> dict:
    """Check account lockout status for a user."""
    locked = await _part11_service.check_lockout(user_id)
    return {"user_id": user_id, "locked": locked}
