"""Parent portal phase 4 — communication, documents, service requests, support."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.parents.enums import (
    ParentCommunicationInboxCategory,
    ParentNotificationPriority,
    ParentServiceRequestCategory,
)


class ParentCommunicationDashboardRead(BaseModel):
    total_notifications: int
    unread_notifications: int
    important_count: int
    examination_notices: int
    attendance_alerts: int
    fee_reminders: int
    service_request_updates: int
    parent_activity_count: int


class ParentNotificationRead(BaseModel):
    notification_key: str
    category: ParentCommunicationInboxCategory
    priority: ParentNotificationPriority = ParentNotificationPriority.NORMAL
    title: str
    body: str
    student_user_id: str | None = None
    student_display_name: str | None = None
    source: str | None = None
    related_request_id: str | None = None
    attachment_refs: list[str] = Field(default_factory=list)
    requires_acknowledgement: bool = False
    published_at: datetime
    expires_at: datetime | None = None
    read: bool
    acknowledged: bool
    delivery_status: str | None = None


class ParentNotificationDetailRead(ParentNotificationRead):
    workflow_ref: str | None = None


class ParentNotificationPreferencesRead(BaseModel):
    email_enabled: bool
    sms_enabled: bool
    push_enabled: bool
    in_app_enabled: bool
    preferred_language: str | None = None
    category_enabled: dict[str, bool] = Field(default_factory=dict)


class ParentNotificationPreferencesUpdate(BaseModel):
    email_enabled: bool | None = None
    sms_enabled: bool | None = None
    push_enabled: bool | None = None
    in_app_enabled: bool | None = None
    preferred_language: str | None = None
    category_enabled: dict[str, bool] | None = None


class ParentDocumentDashboardRead(BaseModel):
    available_documents: int
    recent_publications: int
    pending_requests: int
    awaiting_acknowledgement: int


class ParentDocumentSummaryRead(BaseModel):
    document_id: str
    document_category: str
    document_type: str
    title: str
    academic_year_label: str | None = None
    semester_label: str | None = None
    published_at: datetime | None = None
    requires_acknowledgement: bool = False


class ParentDocumentDownloadRead(BaseModel):
    document_id: str
    document_type: str
    download_token: str
    expires_at: datetime


class ParentDocumentAccessRequestCreate(BaseModel):
    document_category: str = Field(max_length=64)
    document_type: str = Field(max_length=64)
    academic_year_label: str | None = None
    semester_label: str | None = None
    reason: str = Field(min_length=10, max_length=2000)


class ParentDocumentAccessRequestRead(BaseModel):
    request_id: str
    document_category: str
    document_type: str
    status: str
    reason: str
    response_notes: str | None = None
    created_at: datetime


class ParentServiceRequestTypesRead(BaseModel):
    category: ParentServiceRequestCategory
    request_types: list[str]


class ParentServiceRequestCreate(BaseModel):
    category: ParentServiceRequestCategory
    request_type: str = Field(max_length=64)
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=8000)
    priority: str = Field(default="normal", max_length=16)
    supporting_document_refs: list[str] = Field(default_factory=list, max_length=10)


class ParentServiceRequestRead(BaseModel):
    request_id: str
    category: str
    request_type: str
    subject: str
    description: str
    status: str
    priority: str
    assigned_team: str | None = None
    resolution_remarks: str | None = None
    created_at: datetime
    updated_at: datetime


class ParentServiceRequestCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    attachment_refs: list[str] = Field(default_factory=list, max_length=5)


class ParentServiceRequestCommentRead(BaseModel):
    comment_id: str
    author_role: str
    body: str
    created_at: datetime


class ParentSupportEnquiryCreate(BaseModel):
    category: str = Field(max_length=64)
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=8000)


class ParentSupportEnquiryRead(BaseModel):
    enquiry_id: str
    category: str
    subject: str
    status: str
    description: str
    helpdesk_ticket_id: str | None = None
    response_notes: str | None = None
    created_at: datetime


class ParentServiceRequestAdminUpdate(BaseModel):
    status: str | None = None
    assigned_team: str | None = None
    resolution_remarks: str | None = None
    staff_response: str | None = None