import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import Column, String, Text, Boolean, DateTime, Index, func, select, update
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin

logger = logging.getLogger("ipe.compliance.gdpr")


class DSARStatus(StrEnum):
    RECEIVED = "received"
    IN_PROGRESS = "in_progress"
    READY_FOR_REVIEW = "ready_for_review"
    COMPLETED = "completed"
    DENIED = "denied"


class DSARType(StrEnum):
    ACCESS = "access"
    RECTIFICATION = "rectification"
    ERASURE = "erasure"
    PORTABILITY = "portability"
    RESTRICTION = "restriction"
    OBJECTION = "objection"


@dataclass
class DSARRequest:
    request_id: str
    tenant_id: str
    subject_email: str
    request_type: DSARType
    status: DSARStatus = DSARStatus.RECEIVED
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    denial_reason: str = ""
    artifacts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "tenant_id": self.tenant_id,
            "subject_email": self.subject_email,
            "request_type": self.request_type.value,
            "status": self.status.value,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "denial_reason": self.denial_reason,
            "artifacts": self.artifacts,
        }


PII_TABLES: dict[str, list[str]] = {
    "cdm_user": ["email", "full_name", "role"],
    "cdm_customer": ["name", "email"],
    "cdm_supplier": ["name", "contact_email"],
    "cdm_manufacturing_order": ["erp_mo_id"],
    "cdm_demand_line": ["erp_source_id"],
}


class DsarRequestDB(TenantScopedMixin, Base):
    __tablename__ = "gdpr_dsar_request"
    __table_args__ = (
        Index("ix_gdpr_dsar_tenant_status", "tenant_id", "status"),
        Index("ix_gdpr_dsar_tenant_type", "tenant_id", "request_type"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_email = Column(String(320), nullable=False, index=True)
    request_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, server_default="received")
    description = Column(Text, nullable=True)
    denial_reason = Column(Text, nullable=True)
    artifacts = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class DsarConsentDB(TenantScopedMixin, Base):
    __tablename__ = "gdpr_consent"
    __table_args__ = (
        Index("ix_gdpr_consent_tenant_type", "tenant_id", "consent_type"),
        Index("ix_gdpr_consent_subject_type", "subject_email", "consent_type"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_email = Column(String(320), nullable=False, index=True)
    consent_type = Column(String(100), nullable=False)
    granted = Column(Boolean, nullable=False, server_default="true")
    granted_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


def _dsar_to_dict(row: DsarRequestDB) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "tenant_id": str(row.tenant_id),
        "subject_email": row.subject_email,
        "request_type": row.request_type,
        "status": row.status,
        "description": row.description,
        "denial_reason": row.denial_reason,
        "artifacts": row.artifacts or [],
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "completed_at": row.completed_at.isoformat() if row.completed_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _consent_to_dict(row: DsarConsentDB) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "tenant_id": str(row.tenant_id),
        "subject_email": row.subject_email,
        "consent_type": row.consent_type,
        "granted": row.granted,
        "granted_at": row.granted_at.isoformat() if row.granted_at else None,
        "revoked_at": row.revoked_at.isoformat() if row.revoked_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


class DSARService:

    def __init__(self) -> None:
        self._requests: dict[str, DSARRequest] = {}

    def create_request(
        self,
        tenant_id: str,
        subject_email: str,
        request_type: DSARType,
        description: str = "",
    ) -> DSARRequest:
        request = DSARRequest(
            request_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            subject_email=subject_email,
            request_type=request_type,
            description=description,
        )
        self._requests[request.request_id] = request
        logger.info(
            "DSAR request created: id=%s type=%s subject=%s",
            request.request_id,
            request_type.value,
            subject_email,
        )
        return request

    def get_request(self, request_id: str) -> DSARRequest | None:
        return self._requests.get(request_id)

    def list_requests(
        self,
        tenant_id: str | None = None,
        status: DSARStatus | None = None,
    ) -> list[DSARRequest]:
        requests = list(self._requests.values())
        if tenant_id:
            requests = [r for r in requests if r.tenant_id == tenant_id]
        if status:
            requests = [r for r in requests if r.status == status]
        return requests

    def start_processing(self, request_id: str) -> DSARRequest | None:
        request = self._requests.get(request_id)
        if not request:
            return None
        request.status = DSARStatus.IN_PROGRESS
        logger.info("DSAR processing started: id=%s", request_id)
        return request

    def complete_request(
        self,
        request_id: str,
        artifacts: list[dict[str, Any]] | None = None,
    ) -> DSARRequest | None:
        request = self._requests.get(request_id)
        if not request:
            return None
        request.status = DSARStatus.COMPLETED
        request.completed_at = datetime.now(UTC)
        if artifacts:
            request.artifacts = artifacts
        logger.info("DSAR request completed: id=%s", request_id)
        return request

    def deny_request(self, request_id: str, reason: str) -> DSARRequest | None:
        request = self._requests.get(request_id)
        if not request:
            return None
        request.status = DSARStatus.DENIED
        request.denial_reason = reason
        request.completed_at = datetime.now(UTC)
        logger.info("DSAR request denied: id=%s reason=%s", request_id, reason)
        return request

    def get_subject_data_mapping(self) -> dict[str, list[str]]:
        return PII_TABLES

    def calculate_completion_deadline(self, request: DSARRequest) -> datetime:
        from datetime import timedelta
        return request.created_at + timedelta(days=30)


class DsarServiceDB:
    async def create_request(
        self,
        tenant_id: str,
        subject_email: str,
        request_type: DSARType,
        description: str = "",
    ) -> dict[str, Any]:
        from ipe_shared.database.session import get_session

        async for session in get_session():
            row = DsarRequestDB(
                tenant_id=tenant_id,
                subject_email=subject_email,
                request_type=request_type.value,
                status=DSARStatus.RECEIVED.value,
                description=description,
            )
            session.add(row)
            await session.flush()
            await session.commit()
            await session.refresh(row)
            logger.info(
                "DSAR request created: id=%s type=%s subject=%s",
                row.id, request_type.value, subject_email,
            )
            return _dsar_to_dict(row)
        raise RuntimeError("No database session available")

    async def get_request(self, request_id: str) -> dict[str, Any] | None:
        from ipe_shared.database.session import get_session

        async for session in get_session():
            result = await session.execute(
                select(DsarRequestDB).where(DsarRequestDB.id == request_id)
            )
            row = result.scalar_one_or_none()
            return _dsar_to_dict(row) if row else None
        raise RuntimeError("No database session available")

    async def list_requests(
        self,
        tenant_id: str | None = None,
        status: DSARStatus | None = None,
        request_type: DSARType | None = None,
    ) -> list[dict[str, Any]]:
        from ipe_shared.database.session import get_session

        async for session in get_session():
            stmt = select(DsarRequestDB)
            if tenant_id:
                stmt = stmt.where(DsarRequestDB.tenant_id == tenant_id)
            if status:
                stmt = stmt.where(DsarRequestDB.status == status.value)
            if request_type:
                stmt = stmt.where(DsarRequestDB.request_type == request_type.value)
            stmt = stmt.order_by(DsarRequestDB.created_at.desc())
            result = await session.execute(stmt)
            rows = result.scalars().all()
            return [_dsar_to_dict(r) for r in rows]
        raise RuntimeError("No database session available")

    async def start_processing(self, request_id: str) -> dict[str, Any] | None:
        from ipe_shared.database.session import get_session

        async for session in get_session():
            result = await session.execute(
                select(DsarRequestDB).where(DsarRequestDB.id == request_id)
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            row.status = DSARStatus.IN_PROGRESS.value
            await session.flush()
            await session.commit()
            await session.refresh(row)
            logger.info("DSAR processing started: id=%s", request_id)
            return _dsar_to_dict(row)
        raise RuntimeError("No database session available")

    async def complete_request(
        self,
        request_id: str,
        artifacts: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any] | None:
        from ipe_shared.database.session import get_session

        async for session in get_session():
            result = await session.execute(
                select(DsarRequestDB).where(DsarRequestDB.id == request_id)
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            row.status = DSARStatus.COMPLETED.value
            row.completed_at = datetime.now(UTC)
            if artifacts:
                row.artifacts = artifacts
            await session.flush()
            await session.commit()
            await session.refresh(row)
            logger.info("DSAR request completed: id=%s", request_id)
            return _dsar_to_dict(row)
        raise RuntimeError("No database session available")

    async def deny_request(self, request_id: str, reason: str) -> dict[str, Any] | None:
        from ipe_shared.database.session import get_session

        async for session in get_session():
            result = await session.execute(
                select(DsarRequestDB).where(DsarRequestDB.id == request_id)
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            row.status = DSARStatus.DENIED.value
            row.denial_reason = reason
            row.completed_at = datetime.now(UTC)
            await session.flush()
            await session.commit()
            await session.refresh(row)
            logger.info("DSAR request denied: id=%s reason=%s", request_id, reason)
            return _dsar_to_dict(row)
        raise RuntimeError("No database session available")

    async def export_subject_data(self, tenant_id: str, subject_email: str) -> dict[str, Any]:
        from ipe_shared.database.session import get_session

        async for session in get_session():
            stmt = select(DsarRequestDB).where(
                DsarRequestDB.tenant_id == tenant_id,
                DsarRequestDB.subject_email == subject_email,
            )
            result = await session.execute(stmt)
            requests = result.scalars().all()
            return {
                "subject_email": subject_email,
                "tenant_id": tenant_id,
                "requests": [_dsar_to_dict(r) for r in requests],
                "pii_mapping": PII_TABLES,
                "exported_at": datetime.now(UTC).isoformat(),
            }
        raise RuntimeError("No database session available")

    async def delete_subject_data(self, tenant_id: str, subject_email: str) -> dict[str, Any]:
        from ipe_shared.database.session import get_session

        async for session in get_session():
            stmt = select(DsarRequestDB).where(
                DsarRequestDB.tenant_id == tenant_id,
                DsarRequestDB.subject_email == subject_email,
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()
            count = len(rows)
            for row in rows:
                await session.delete(row)
            await session.commit()
            logger.info(
                "Deleted %d DSAR records for subject=%s tenant=%s",
                count, subject_email, tenant_id,
            )
            return {
                "subject_email": subject_email,
                "tenant_id": tenant_id,
                "deleted_request_count": count,
                "deleted_at": datetime.now(UTC).isoformat(),
            }
        raise RuntimeError("No database session available")


class ConsentManager:
    async def grant_consent(
        self,
        tenant_id: str,
        subject_email: str,
        consent_type: str,
    ) -> dict[str, Any]:
        from ipe_shared.database.session import get_session

        async for session in get_session():
            result = await session.execute(
                select(DsarConsentDB).where(
                    DsarConsentDB.tenant_id == tenant_id,
                    DsarConsentDB.subject_email == subject_email,
                    DsarConsentDB.consent_type == consent_type,
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.granted = True
                existing.granted_at = datetime.now(UTC)
                existing.revoked_at = None
                await session.flush()
                await session.commit()
                await session.refresh(existing)
                logger.info("Consent re-granted: subject=%s type=%s", subject_email, consent_type)
                return _consent_to_dict(existing)
            row = DsarConsentDB(
                tenant_id=tenant_id,
                subject_email=subject_email,
                consent_type=consent_type,
                granted=True,
                granted_at=datetime.now(UTC),
            )
            session.add(row)
            await session.flush()
            await session.commit()
            await session.refresh(row)
            logger.info("Consent granted: subject=%s type=%s", subject_email, consent_type)
            return _consent_to_dict(row)
        raise RuntimeError("No database session available")

    async def revoke_consent(
        self,
        tenant_id: str,
        subject_email: str,
        consent_type: str,
    ) -> dict[str, Any] | None:
        from ipe_shared.database.session import get_session

        async for session in get_session():
            result = await session.execute(
                select(DsarConsentDB).where(
                    DsarConsentDB.tenant_id == tenant_id,
                    DsarConsentDB.subject_email == subject_email,
                    DsarConsentDB.consent_type == consent_type,
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            row.granted = False
            row.revoked_at = datetime.now(UTC)
            await session.flush()
            await session.commit()
            await session.refresh(row)
            logger.info("Consent revoked: subject=%s type=%s", subject_email, consent_type)
            return _consent_to_dict(row)
        raise RuntimeError("No database session available")

    async def check_consent(
        self,
        tenant_id: str,
        subject_email: str,
        consent_type: str,
    ) -> bool | None:
        from ipe_shared.database.session import get_session

        async for session in get_session():
            result = await session.execute(
                select(DsarConsentDB).where(
                    DsarConsentDB.tenant_id == tenant_id,
                    DsarConsentDB.subject_email == subject_email,
                    DsarConsentDB.consent_type == consent_type,
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return row.granted
        raise RuntimeError("No database session available")