"""Support access API schemas."""

from datetime import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field

from app.modules.support_access.models import (
    SupportAccessActivity,
    SupportAccessRequest,
    SupportAccessSession,
)


class SupportAccessRequestCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    tenant_id: PydanticObjectId
    reason: str = Field(min_length=10, max_length=500)
    scopes: list[str] = Field(min_length=1, max_length=4)
    duration_minutes: int = Field(default=60, ge=15, le=480)


class SupportAccessApprovalRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    decision: str = Field(pattern=r"^(approved|rejected)$")
    notes: str | None = Field(default=None, max_length=500)


class SupportAccessRequestRead(BaseModel):
    id: str
    requester_id: str
    tenant_id: str
    reason: str
    scopes: list[str]
    duration_minutes: int
    status: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_document(cls, doc: SupportAccessRequest) -> "SupportAccessRequestRead":
        return cls(
            id=str(doc.id),
            requester_id=str(doc.requester_id),
            tenant_id=str(doc.tenant_id),
            reason=doc.reason,
            scopes=doc.scopes,
            duration_minutes=doc.duration_minutes,
            status=doc.status,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )


class SupportAccessSessionRead(BaseModel):
    id: str
    request_id: str
    operator_id: str
    tenant_id: str
    scopes: list[str]
    expires_at: datetime
    started_at: datetime
    ended_at: datetime | None
    revoked_at: datetime | None
    token: str | None = None

    @classmethod
    def from_document(cls, session: SupportAccessSession, *, token: str | None) -> "SupportAccessSessionRead":
        return cls(
            id=str(session.id),
            request_id=str(session.request_id),
            operator_id=str(session.operator_id),
            tenant_id=str(session.tenant_id),
            scopes=session.scopes,
            expires_at=session.expires_at,
            started_at=session.started_at,
            ended_at=session.ended_at,
            revoked_at=session.revoked_at,
            token=token,
        )


class SupportActivityRead(BaseModel):
    id: str
    action: str
    resource_type: str
    resource_id: str | None
    created_at: datetime

    @classmethod
    def from_document(cls, row: SupportAccessActivity) -> "SupportActivityRead":
        return cls(
            id=str(row.id),
            action=row.action,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            created_at=row.created_at,
        )
