"""Department Admin phase 9 — documents and audit visibility."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.department_admin.models import (
    DepartmentDocumentAccessScope,
    DepartmentDocumentStatus,
)


class DocumentUploadBody(BaseModel):
    title: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    category: str = Field(max_length=64)
    tags: list[str] = Field(default_factory=list)
    access_scope: DepartmentDocumentAccessScope = DepartmentDocumentAccessScope.DEPT_ADMIN_ONLY
    programme_code: str | None = Field(default=None, max_length=32)
    batch_label: str | None = Field(default=None, max_length=64)
    section_code: str | None = Field(default=None, max_length=16)
    authorized_user_ids: list[str] = Field(default_factory=list, max_length=200)
    academic_year_label: str | None = Field(default=None, max_length=32)
    related_entity_type: str | None = Field(default=None, max_length=64)
    related_entity_id: str | None = Field(default=None, max_length=128)
    file_name: str = Field(max_length=256)
    mime_type: str = Field(max_length=128)
    file_content_base64: str
    idempotency_key: str | None = Field(default=None, max_length=128)


class DocumentUpdateBody(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    category: str | None = Field(default=None, max_length=64)
    tags: list[str] | None = None
    access_scope: DepartmentDocumentAccessScope | None = None
    programme_code: str | None = Field(default=None, max_length=32)
    batch_label: str | None = Field(default=None, max_length=64)
    section_code: str | None = Field(default=None, max_length=16)
    authorized_user_ids: list[str] | None = None
    academic_year_label: str | None = Field(default=None, max_length=32)
    related_entity_type: str | None = Field(default=None, max_length=64)
    related_entity_id: str | None = Field(default=None, max_length=128)
    status: DepartmentDocumentStatus | None = None


class DocumentVersionBody(BaseModel):
    file_name: str = Field(max_length=256)
    mime_type: str = Field(max_length=128)
    file_content_base64: str
    update_reason: str | None = Field(default=None, max_length=500)
    idempotency_key: str | None = Field(default=None, max_length=128)


class DocumentArchiveBody(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class DocumentRead(BaseModel):
    document_id: str
    title: str
    description: str | None
    category: str
    tags: list[str]
    access_scope: DepartmentDocumentAccessScope
    programme_code: str | None
    batch_label: str | None
    section_code: str | None
    authorized_user_ids: list[str]
    academic_year_label: str | None
    related_entity_type: str | None
    related_entity_id: str | None
    status: DepartmentDocumentStatus
    current_version: int
    file_name: str
    mime_type: str
    file_size: int
    uploaded_by: str
    created_at: datetime
    updated_at: datetime
    checksum: str


class DocumentVersionRead(BaseModel):
    version_id: str
    version_number: int
    file_name: str
    mime_type: str
    file_size: int
    checksum: str
    uploaded_by: str
    update_reason: str | None
    created_at: datetime
    previous_version_id: str | None


class DocumentHistoryRead(BaseModel):
    event_id: str
    event_type: str
    actor_user_id: str | None
    summary: str | None
    metadata: dict
    created_at: datetime


class DocumentDownloadRead(BaseModel):
    document_id: str
    version_number: int
    file_name: str
    content_type: str
    content_base64: str
    checksum: str


class DocumentListFilters(BaseModel):
    q: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, max_length=64)
    status: DepartmentDocumentStatus | None = None
    access_scope: DepartmentDocumentAccessScope | None = None
    academic_year_label: str | None = Field(default=None, max_length=32)
    programme_code: str | None = Field(default=None, max_length=32)
    uploaded_by: str | None = None
    tag: str | None = Field(default=None, max_length=64)
    date_from: datetime | None = None
    date_to: datetime | None = None

    @field_validator("date_to")
    @classmethod
    def range_ok(cls, date_to: datetime | None, info) -> datetime | None:
        start = info.data.get("date_from")
        if start and date_to and start > date_to:
            raise ValueError("date_from must be on or before date_to")
        return date_to


class AuditListFilters(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    actor_id: str | None = None
    action_category: str | None = Field(default=None, max_length=64)
    action: str | None = Field(default=None, max_length=128)
    resource_type: str | None = Field(default=None, max_length=64)
    outcome: str | None = Field(default=None, max_length=32)
    module: str | None = Field(default=None, max_length=64)
    resource_id: str | None = Field(default=None, max_length=128)

    @field_validator("date_to")
    @classmethod
    def range_ok(cls, date_to: datetime | None, info) -> datetime | None:
        start = info.data.get("date_from")
        if start and date_to and start > date_to:
            raise ValueError("date_from must be on or before date_to")
        return date_to


class DepartmentAuditRead(BaseModel):
    event_id: str
    actor_id: str | None
    actor_role: str | None
    action: str
    action_category: str
    resource_type: str
    resource_id: str | None
    outcome: str
    request_id: str | None
    metadata: dict
    created_at: datetime


class AuditSummaryRead(BaseModel):
    total_events: int
    by_outcome: dict[str, int]
    by_action_category: dict[str, int]
    window_start: datetime | None
    window_end: datetime | None
    advisory: str


class SecurityEventDeptRead(BaseModel):
    event_id: str
    code: str
    category: str
    severity: str
    title: str
    description: str
    status: str
    created_at: datetime


class ConfigurationChangeRead(BaseModel):
    setting_key: str
    previous_value: object | None
    new_value: object | None
    changed_by: str | None
    changed_at: datetime


class EffectivePermissionsRead(BaseModel):
    permissions: list[str]
    advisory: str


class AuditExportBody(BaseModel):
    filters: AuditListFilters = Field(default_factory=AuditListFilters)
    max_rows: int = Field(default=5000, ge=1, le=20000)


class AuditExportRead(BaseModel):
    export_id: str
    row_count: int
    content_type: str
    file_name: str
    content_base64: str
    expires_at: datetime | None