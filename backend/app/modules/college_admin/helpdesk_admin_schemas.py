"""Helpdesk administration API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.college_admin.helpdesk_admin_models import RequesterAudience, SupportPriority, SupportTicketStatus


class SupportTicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=8000)
    category_code: str
    module_key: str
    issue_type: str
    priority: SupportPriority = SupportPriority.NORMAL
    requester_user_id: str | None = None
    requester_audience: RequesterAudience = RequesterAudience.INSTITUTION
    idempotency_key: str | None = Field(default=None, max_length=128)


class SupportTicketUpdate(BaseModel):
    status: SupportTicketStatus | None = None
    priority: SupportPriority | None = None


class SupportAssignRequest(BaseModel):
    assignee_user_id: str | None = None
    assigned_team: str | None = None


class SupportCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class SupportInternalNoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class SupportAttachmentCreate(BaseModel):
    file_name: str
    mime_type: str = "application/pdf"
    content_base64: str


class SupportEscalateRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
    target_team: str


class SupportResolveRequest(BaseModel):
    resolution_detail: str = Field(min_length=3, max_length=4000)


class SupportReopenRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class SupportSlaStatus(BaseModel):
    ticket_id: str
    first_response_due_at: datetime | None
    resolution_due_at: datetime | None
    is_overdue: bool


class SupportTicketRead(BaseModel):
    ticket_id: str
    ticket_number: str
    title: str
    description: str
    category_code: str
    module_key: str
    issue_type: str
    priority: SupportPriority
    status: SupportTicketStatus
    requester_user_id: str
    requester_audience: RequesterAudience
    assigned_user_id: str | None
    assigned_team: str | None
    first_response_due_at: datetime | None
    resolution_due_at: datetime | None
    is_overdue: bool
    resolved_at: datetime | None
    resolution_detail: str | None
    created_at: datetime
    updated_at: datetime
    comments: list[dict] | None = None
    internal_notes: list[dict] | None = None
    attachments: list[dict] | None = None


class SupportHistoryItem(BaseModel):
    change_type: str
    actor_id: str | None
    summary: str
    created_at: datetime


class SupportPerformanceReport(BaseModel):
    open_count: int
    overdue_count: int
    resolved_last_7d: int
    avg_resolution_hours: float | None


class SupportCategoryRead(BaseModel):
    category_code: str
    title: str
    module_key: str
    issue_type: str