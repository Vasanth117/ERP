"""HR employee document management."""

from datetime import date, datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import HrEmployeeDocumentStatus


class HrDocumentCategory(Document):
    tenant_id: PydanticObjectId
    category_code: str = Field(max_length=64)
    name: str = Field(max_length=200)
    parent_group: str = Field(max_length=64)
    description: str | None = Field(default=None, max_length=2000)
    allowed_extensions: list[str] = Field(default_factory=lambda: ["pdf", "jpg", "jpeg", "png"])
    is_sensitive: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_document_categories"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("category_code", ASCENDING)],
                unique=True,
                name="unique_hr_doc_category",
            ),
        ]


class HrMandatoryDocumentRule(Document):
    tenant_id: PydanticObjectId
    rule_code: str = Field(max_length=64)
    category_code: str = Field(max_length=64)
    employment_category_code: str | None = None
    employment_type_code: str | None = None
    employment_stage: str | None = Field(default=None, max_length=64)
    is_mandatory: bool = True
    is_active: bool = True
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_mandatory_document_rules"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("rule_code", ASCENDING)],
                unique=True,
                name="unique_mandatory_doc_rule",
            ),
        ]


class HrDocumentExpiryPolicy(Document):
    tenant_id: PydanticObjectId
    reminder_days: int = Field(default=30, ge=1, le=365)
    updated_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_document_expiry_policies"
        indexes = [
            IndexModel([("tenant_id", ASCENDING)], unique=True, name="unique_hr_doc_expiry_policy"),
        ]


class HrEmployeeDocument(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    category_code: str = Field(max_length=64)
    document_code: str = Field(max_length=64)
    title: str = Field(max_length=200)
    storage_key: str
    file_name: str = Field(max_length=260)
    mime_type: str = Field(max_length=120)
    file_size: int = Field(ge=1)
    issue_date: date | None = None
    expires_on: date | None = None
    issuing_authority: str | None = Field(default=None, max_length=200)
    remarks: str | None = Field(default=None, max_length=2000)
    status: HrEmployeeDocumentStatus = HrEmployeeDocumentStatus.PENDING_VERIFICATION
    is_mandatory: bool = False
    previous_document_id: PydanticObjectId | None = None
    replaced_by_document_id: PydanticObjectId | None = None
    verified_by: PydanticObjectId | None = None
    verified_at: datetime | None = None
    rejection_reason: str | None = Field(default=None, max_length=2000)
    submitted_by: PydanticObjectId | None = None
    submitted_at: datetime | None = None
    archived_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_employee_documents"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("document_code", ASCENDING), ("status", ASCENDING)],
                name="hr_documents_by_user_code",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("status", ASCENDING)],
                name="hr_documents_by_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("category_code", ASCENDING)],
                name="hr_documents_by_category",
            ),
        ]


class HrEmployeeDocumentEvent(Document):
    tenant_id: PydanticObjectId
    document_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    event_type: str = Field(max_length=64)
    status_from: str | None = None
    status_to: str | None = None
    note: str | None = Field(default=None, max_length=2000)
    actor_id: PydanticObjectId | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_employee_document_events"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("document_id", ASCENDING), ("created_at", DESCENDING)],
                name="hr_doc_events_by_document",
            ),
        ]