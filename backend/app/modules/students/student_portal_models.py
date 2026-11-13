"""Student portal — library, services, communication, documents, reports (non-authoritative)."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.students.student_portal_enums import (
    StudentDocumentPortalType,
    StudentDocumentRequestStatus,
    StudentReportExportStatus,
    StudentReportType,
    StudentServiceCategory,
    StudentServiceRequestStatus,
)


class StudentServiceRequest(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    request_id: str
    service_id: str | None = None
    category: StudentServiceCategory
    title: str = Field(max_length=200)
    description: str = Field(max_length=4000)
    payload: dict = Field(default_factory=dict)
    status: StudentServiceRequestStatus = StudentServiceRequestStatus.SUBMITTED
    official_ref: str | None = Field(default=None, description="Central module request id")
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_service_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("request_id", ASCENDING)],
                unique=True,
                name="unique_student_service_request",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="service_requests_by_student",
            ),
        ]


class StudentServiceRequestHistory(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    request_id: str
    from_status: str
    to_status: str
    note: str | None = Field(default=None, max_length=1000)
    recorded_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_service_request_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("request_id", ASCENDING), ("recorded_at", DESCENDING)],
                name="service_request_history",
            ),
        ]


class StudentHostelRequestReference(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    portal_request_id: str
    official_request_id: str
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_hostel_request_references"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("portal_request_id", ASCENDING)],
                unique=True,
                name="unique_hostel_req_ref",
            ),
        ]


class StudentTransportRequestReference(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    portal_request_id: str
    official_request_id: str
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_transport_request_references"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("portal_request_id", ASCENDING)],
                unique=True,
                name="unique_transport_req_ref",
            ),
        ]


class StudentLibraryActivityView(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    activity_type: str
    reference_id: str
    title: str
    viewed_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_library_activity_views"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("viewed_at", DESCENDING)],
                name="library_activity_views",
            ),
        ]


class StudentCommunicationPreferences(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    email_enabled: bool = True
    push_enabled: bool = False
    academic_enabled: bool = True
    finance_enabled: bool = True
    examination_enabled: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_communication_preferences"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_student_comm_prefs",
            ),
        ]


class StudentNotificationReadStatus(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    notification_key: str
    source: str
    read_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_notification_read_status"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("notification_key", ASCENDING)],
                unique=True,
                name="unique_notification_read",
            ),
        ]


class StudentDocumentReference(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    document_id: str
    document_type: str
    title: str
    authorized: bool = True
    storage_token: str | None = None
    last_viewed_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_document_references"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("document_id", ASCENDING)],
                unique=True,
                name="unique_student_doc_ref",
            ),
        ]


class StudentDocumentRequest(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    request_id: str
    request_type: StudentDocumentPortalType
    reason: str | None = Field(default=None, max_length=2000)
    status: StudentDocumentRequestStatus = StudentDocumentRequestStatus.SUBMITTED
    fulfilled_document_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_document_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("request_id", ASCENDING)],
                unique=True,
                name="unique_student_document_request",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="document_requests_by_student",
            ),
        ]


class StudentProfileCorrectionRequest(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    request_id: str
    field_name: str = Field(max_length=64)
    proposed_value: str = Field(max_length=500)
    reason: str = Field(max_length=2000)
    status: StudentDocumentRequestStatus = StudentDocumentRequestStatus.SUBMITTED
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_profile_correction_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("request_id", ASCENDING)],
                unique=True,
                name="unique_profile_correction_request",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="profile_corrections_by_student",
            ),
        ]


class StudentReportExport(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    export_id: str
    report_type: StudentReportType
    status: StudentReportExportStatus = StudentReportExportStatus.PENDING
    storage_key: str | None = None
    summary: dict = Field(default_factory=dict)
    error_message: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    ready_at: datetime | None = None
    expires_at: datetime | None = None

    class Settings:
        name = "student_report_exports"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("export_id", ASCENDING)],
                unique=True,
                name="unique_student_report_export",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="report_exports_by_student",
            ),
        ]


class StudentReportDownloadLog(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    export_id: str
    downloaded_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_report_download_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("downloaded_at", DESCENDING)],
                name="report_download_logs",
            ),
        ]
