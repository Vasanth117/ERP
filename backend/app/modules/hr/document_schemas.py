"""HR document API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.hr.document_models import HrDocumentCategory, HrEmployeeDocument
from app.modules.hr.enums import HrEmployeeDocumentStatus


class HrDocumentCategoryRead(BaseModel):
    category_code: str
    name: str
    parent_group: str
    description: str | None
    is_sensitive: bool
    is_active: bool

    @classmethod
    def from_doc(cls, doc: HrDocumentCategory) -> "HrDocumentCategoryRead":
        return cls(
            category_code=doc.category_code,
            name=doc.name,
            parent_group=doc.parent_group,
            description=doc.description,
            is_sensitive=doc.is_sensitive,
            is_active=doc.is_active,
        )


class EmployeeDocumentRead(BaseModel):
    document_id: str
    employee_user_id: str
    category_code: str
    document_code: str
    title: str
    file_name: str
    mime_type: str
    file_size: int
    issue_date: date | None
    expires_on: date | None
    issuing_authority: str | None
    remarks: str | None
    status: HrEmployeeDocumentStatus
    is_mandatory: bool
    rejection_reason: str | None
    submitted_at: datetime | None
    verified_at: datetime | None

    @classmethod
    def from_doc(cls, doc: HrEmployeeDocument) -> "EmployeeDocumentRead":
        return cls(
            document_id=str(doc.id),
            employee_user_id=str(doc.employee_user_id),
            category_code=doc.category_code,
            document_code=doc.document_code,
            title=doc.title,
            file_name=doc.file_name,
            mime_type=doc.mime_type,
            file_size=doc.file_size,
            issue_date=doc.issue_date,
            expires_on=doc.expires_on,
            issuing_authority=doc.issuing_authority,
            remarks=doc.remarks,
            status=doc.status,
            is_mandatory=doc.is_mandatory,
            rejection_reason=doc.rejection_reason,
            submitted_at=doc.submitted_at,
            verified_at=doc.verified_at,
        )


class DocumentUploadMeta(BaseModel):
    employee_user_id: str
    category_code: str
    document_code: str | None = None
    title: str = Field(min_length=1, max_length=200)
    issue_date: date | None = None
    expires_on: date | None = None
    issuing_authority: str | None = None
    remarks: str | None = None
    replace_document_id: str | None = None
    submit_for_verification: bool = True


class DocumentVerificationDecision(BaseModel):
    decision: HrEmployeeDocumentStatus
    reason: str | None = Field(default=None, max_length=2000)


class EmployeeDocumentOverview(BaseModel):
    total: int = 0
    submitted: int = 0
    verified: int = 0
    pending_verification: int = 0
    rejected: int = 0
    missing_mandatory: int = 0
    expired: int = 0
    expiring_soon: int = 0
    by_category: dict[str, int] = Field(default_factory=dict)


class MandatoryDocumentStatus(BaseModel):
    category_code: str
    rule_code: str
    submitted: bool
    document_id: str | None = None
    status: str | None = None
    expires_on: date | None = None


class DocumentEventRead(BaseModel):
    event_type: str
    status_from: str | None
    status_to: str | None
    note: str | None
    actor_id: str | None
    created_at: datetime


class ExpiryPolicyUpsert(BaseModel):
    reminder_days: int = Field(default=30, ge=1, le=365)


class MandatoryRuleUpsert(BaseModel):
    rule_code: str
    category_code: str
    employment_category_code: str | None = None
    employment_type_code: str | None = None
    employment_stage: str | None = None
    is_mandatory: bool = True