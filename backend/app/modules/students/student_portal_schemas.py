"""Student portal phase 10 API schemas."""

from datetime import date, datetime, time

from pydantic import BaseModel, Field


class LibraryCatalogRead(BaseModel):
    book_id: str
    title: str
    authors: list[str]
    isbn: str | None = None
    category: str | None = None
    available_copies: int


class LibraryIssuedBookRead(BaseModel):
    circulation_id: str
    book_id: str
    title: str
    issued_at: datetime
    due_at: date
    status: str
    overdue: bool


class LibraryFineRead(BaseModel):
    fine_id: str
    amount: float
    reason: str
    status: str


class DigitalResourceRead(BaseModel):
    resource_id: str
    title: str
    description: str | None = None
    url: str | None = None


class HostelApplicationRead(BaseModel):
    application_id: str
    status: str
    submitted_at: datetime


class HostelAllocationRead(BaseModel):
    hostel_name: str
    block: str
    room_number: str
    bed_label: str
    fee_amount: float


class HostelRequestInput(BaseModel):
    request_type: str
    description: str = Field(min_length=3, max_length=4000)

    model_config = {"extra": "forbid"}


class TransportRouteRead(BaseModel):
    route_id: str
    name: str
    fee_amount: float


class TransportStopRead(BaseModel):
    stop_id: str
    name: str
    pickup_time: time | None = None
    drop_time: time | None = None
    sequence: int


class TransportAllocationRead(BaseModel):
    route_id: str
    route_name: str
    pickup_stop: str
    drop_stop: str
    fee_amount: float


class TransportRequestInput(BaseModel):
    request_type: str
    description: str = Field(min_length=3, max_length=4000)

    model_config = {"extra": "forbid"}


class InstitutionalServiceRead(BaseModel):
    service_id: str
    title: str
    category: str
    description: str | None = None


class ServiceRequestInput(BaseModel):
    service_id: str
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=4000)

    model_config = {"extra": "forbid"}


class ServiceRequestRead(BaseModel):
    request_id: str
    category: str
    title: str
    status: str
    created_at: datetime


class AnnouncementFeedRead(BaseModel):
    id: str
    scope: str
    title: str
    body: str
    course_code: str | None = None
    created_at: datetime
    read: bool


class NotificationFeedRead(BaseModel):
    notification_key: str
    source: str
    title: str
    body: str
    created_at: datetime
    read: bool


class CommunicationPreferencesRead(BaseModel):
    email_enabled: bool
    push_enabled: bool
    academic_enabled: bool
    finance_enabled: bool
    examination_enabled: bool


class CommunicationPreferencesUpdate(BaseModel):
    email_enabled: bool | None = None
    push_enabled: bool | None = None
    academic_enabled: bool | None = None
    finance_enabled: bool | None = None
    examination_enabled: bool | None = None

    model_config = {"extra": "forbid"}


class StudentDocumentPortalRead(BaseModel):
    document_id: str
    document_type: str
    title: str


class DocumentRequestInput(BaseModel):
    request_type: str
    reason: str | None = Field(default=None, max_length=2000)

    model_config = {"extra": "forbid"}


class ProfileCorrectionInput(BaseModel):
    field_name: str = Field(min_length=2, max_length=64)
    proposed_value: str = Field(min_length=1, max_length=500)
    reason: str = Field(min_length=3, max_length=2000)

    model_config = {"extra": "forbid"}


class ReportGenerateInput(BaseModel):
    report_type: str

    model_config = {"extra": "forbid"}


class ReportExportRead(BaseModel):
    export_id: str
    report_type: str
    status: str
    created_at: datetime
    ready_at: datetime | None = None
    download_token: str | None = None
