"""HR access scope, temporary grants, reviews and audit exports."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import HrAccessScopeKind, HrTemporaryAccessStatus


class HrAccessScopeAssignment(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    scope_kind: HrAccessScopeKind = HrAccessScopeKind.INSTITUTION
    department_id: PydanticObjectId | None = None
    campus_id: PydanticObjectId | None = None
    employee_user_ids: list[PydanticObjectId] = Field(default_factory=list)
    role_profile_code: str | None = Field(default=None, max_length=64)
    actor_id: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_access_assignments"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("user_id", ASCENDING)], unique=True, name="unique_hr_access_assignment"),
        ]


class HrRolePermissionMapping(Document):
    """Institution overlay on platform RBAC (does not replace Role enum)."""

    tenant_id: PydanticObjectId
    role_profile_code: str = Field(max_length=64)
    title: str = Field(max_length=200)
    permission_codes: list[str] = Field(default_factory=list)
    separation_rules: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    actor_id: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_role_permission_mappings"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("role_profile_code", ASCENDING)], unique=True, name="unique_hr_role_profile"),
        ]


class HrTemporaryAccessGrant(Document):
    tenant_id: PydanticObjectId
    grant_code: str = Field(max_length=64)
    subject_user_id: PydanticObjectId
    granted_permissions: list[str] = Field(default_factory=list)
    scope: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(max_length=2000)
    status: HrTemporaryAccessStatus = HrTemporaryAccessStatus.PENDING
    starts_at: datetime
    expires_at: datetime
    approver_id: PydanticObjectId | None = None
    approved_at: datetime | None = None
    revoked_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_temporary_access_grants"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("grant_code", ASCENDING)], unique=True, name="unique_hr_temp_grant"),
            IndexModel([("tenant_id", ASCENDING), ("subject_user_id", ASCENDING), ("status", ASCENDING)], name="hr_temp_grant_subject"),
        ]


class HrAccessReviewRecord(Document):
    tenant_id: PydanticObjectId
    review_code: str = Field(max_length=64)
    subject_user_id: PydanticObjectId
    reviewer_id: PydanticObjectId
    findings: dict[str, Any] = Field(default_factory=dict)
    decision: str = Field(max_length=64)
    notes: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None

    class Settings:
        name = "hr_access_review_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("review_code", ASCENDING)], unique=True, name="unique_hr_access_review"),
        ]


class HrAuditExportHistory(Document):
    tenant_id: PydanticObjectId
    export_code: str = Field(max_length=64)
    filters: dict[str, Any] = Field(default_factory=dict)
    row_count: int = 0
    file_content_base64: str | None = None
    retention_until: datetime | None = None
    legal_hold: bool = False
    actor_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_audit_export_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("export_code", ASCENDING)], unique=True, name="unique_hr_audit_export"),
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)], name="hr_audit_exports_recent"),
        ]