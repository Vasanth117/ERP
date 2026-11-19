"""Schemas for HR audit and access management."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hr.enums import HrAccessScopeKind, HrTemporaryAccessStatus
from app.modules.hr.hr_audit_models import (
    HrAccessReviewRecord,
    HrAccessScopeAssignment,
    HrAuditExportHistory,
    HrRolePermissionMapping,
    HrTemporaryAccessGrant,
)


class HrAuditDashboard(BaseModel):
    total_activities: int = 0
    institution_audit_entries: int = 0
    by_activity_type: dict[str, int] = Field(default_factory=dict)
    pending_acknowledgements: int = 0
    active_temporary_grants: int = 0


class HrAuditSearch(BaseModel):
    employee_user_id: str | None = None
    actor_id: str | None = None
    department_id: str | None = None
    activity_type: str | None = None
    module: str | None = None
    action_prefix: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class HrAuditEntryRead(BaseModel):
    source: str
    action: str
    summary: str
    actor_id: str | None
    employee_user_id: str | None
    resource_type: str | None
    resource_id: str | None
    module: str | None
    outcome: str | None
    metadata: dict[str, Any]
    created_at: datetime


class AccessScopeAssignmentUpsert(BaseModel):
    user_id: str
    scope_kind: HrAccessScopeKind = HrAccessScopeKind.INSTITUTION
    department_id: str | None = None
    campus_id: str | None = None
    employee_user_ids: list[str] = Field(default_factory=list)
    role_profile_code: str | None = None


class AccessScopeAssignmentRead(BaseModel):
    user_id: str
    scope_kind: HrAccessScopeKind
    department_id: str | None
    campus_id: str | None
    employee_user_ids: list[str]
    role_profile_code: str | None
    updated_at: datetime

    @classmethod
    def from_doc(cls, doc: HrAccessScopeAssignment) -> "AccessScopeAssignmentRead":
        return cls(
            user_id=str(doc.user_id),
            scope_kind=doc.scope_kind,
            department_id=str(doc.department_id) if doc.department_id else None,
            campus_id=str(doc.campus_id) if doc.campus_id else None,
            employee_user_ids=[str(x) for x in doc.employee_user_ids],
            role_profile_code=doc.role_profile_code,
            updated_at=doc.updated_at,
        )


class RoleProfileRead(BaseModel):
    role_profile_code: str
    title: str
    permission_codes: list[str]
    platform_note: str | None = None


class RoleProfileUpsert(BaseModel):
    role_profile_code: str = Field(max_length=64)
    title: str = Field(max_length=200)
    permission_codes: list[str] = Field(default_factory=list)
    separation_rules: dict[str, Any] = Field(default_factory=dict)


class TemporaryAccessCreate(BaseModel):
    grant_code: str = Field(max_length=64)
    subject_user_id: str
    granted_permissions: list[str] = Field(default_factory=list)
    scope: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(max_length=2000)
    starts_at: datetime
    expires_at: datetime


class TemporaryAccessRead(BaseModel):
    id: str
    grant_code: str
    subject_user_id: str
    granted_permissions: list[str]
    status: HrTemporaryAccessStatus
    starts_at: datetime
    expires_at: datetime
    reason: str

    @classmethod
    def from_doc(cls, doc: HrTemporaryAccessGrant) -> "TemporaryAccessRead":
        return cls(
            id=str(doc.id),
            grant_code=doc.grant_code,
            subject_user_id=str(doc.subject_user_id),
            granted_permissions=doc.granted_permissions,
            status=doc.status,
            starts_at=doc.starts_at,
            expires_at=doc.expires_at,
            reason=doc.reason,
        )


class AccessReviewCreate(BaseModel):
    review_code: str = Field(max_length=64)
    subject_user_id: str
    findings: dict[str, Any] = Field(default_factory=dict)
    decision: str = Field(max_length=64)
    notes: str | None = None


class AccessReviewRead(BaseModel):
    review_code: str
    subject_user_id: str
    reviewer_id: str
    decision: str
    notes: str | None
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_doc(cls, doc: HrAccessReviewRecord) -> "AccessReviewRead":
        return cls(
            review_code=doc.review_code,
            subject_user_id=str(doc.subject_user_id),
            reviewer_id=str(doc.reviewer_id),
            decision=doc.decision,
            notes=doc.notes,
            created_at=doc.created_at,
            completed_at=doc.completed_at,
        )


class AuditExportRequest(BaseModel):
    filters: HrAuditSearch = Field(default_factory=HrAuditSearch)
    retention_days: int = 90


class AuditExportRead(BaseModel):
    export_code: str
    row_count: int
    file_content_base64: str
    created_at: datetime

    @classmethod
    def from_doc(cls, doc: HrAuditExportHistory, content: str) -> "AuditExportRead":
        return cls(
            export_code=doc.export_code,
            row_count=doc.row_count,
            file_content_base64=content,
            created_at=doc.created_at,
        )