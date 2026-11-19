"""Parent / guardian portal MongoDB collections."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.parents.enums import (
    ParentAccountStatus,
    ParentContactVerificationChannel,
    ParentContactVerificationStatus,
    ParentLinkRequestStatus,
    ParentProfileChangeStatus,
    ParentRelationshipStatus,
    ParentRelationshipType,
    ParentVerificationMethod,
)


class ParentAddress(BaseModel):
    line1: str | None = Field(default=None, max_length=200)
    line2: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=80)
    state: str | None = Field(default=None, max_length=80)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=80)


class ParentCommunicationPreferences(BaseModel):
    email_enabled: bool = True
    sms_enabled: bool = True
    push_enabled: bool = True
    preferred_language: str | None = Field(default=None, max_length=16)
    announcement_categories: list[str] = Field(default_factory=list)


class ParentProfile(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    display_name: str | None = Field(default=None, max_length=200)
    contact_phone: str | None = Field(default=None, max_length=32)
    alternate_email: str | None = Field(default=None, max_length=254)
    address: ParentAddress | None = None
    profile_photo_ref: str | None = None
    communication_preferences: ParentCommunicationPreferences = Field(
        default_factory=ParentCommunicationPreferences
    )
    account_status: ParentAccountStatus = ParentAccountStatus.PENDING_ACTIVATION
    email_verified: bool = False
    mobile_verified: bool = False
    identity_verified: bool = False
    activated_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_profiles"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_parent_profile_per_user",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("contact_phone", ASCENDING)],
                name="parent_phone_lookup",
                sparse=True,
            ),
        ]


class ParentAccountStatusHistory(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    from_status: ParentAccountStatus | None = None
    to_status: ParentAccountStatus
    reason: str | None = Field(default=None, max_length=500)
    changed_by: PydanticObjectId | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_account_status_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="parent_status_history",
            ),
        ]


class ParentContactVerification(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    channel: ParentContactVerificationChannel
    target_value: str = Field(max_length=254)
    token_hash: str
    status: ParentContactVerificationStatus = ParentContactVerificationStatus.PENDING
    expires_at: datetime
    verified_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_contact_verifications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("channel", ASCENDING)],
                name="parent_verifications_by_user",
            ),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, name="parent_verification_ttl"),
        ]


class ParentProfileChangeRequest(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    requested_fields: dict[str, Any]
    reason: str | None = Field(default=None, max_length=1000)
    status: ParentProfileChangeStatus = ParentProfileChangeStatus.PENDING
    reviewed_by: PydanticObjectId | None = None
    review_notes: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_profile_change_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("status", ASCENDING)],
                name="parent_profile_changes",
            ),
        ]


class ParentStudentLinkRequest(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    relationship_type: ParentRelationshipType
    relationship_declaration: str = Field(max_length=2000)
    reference_type: str = Field(max_length=32)
    reference_value: str = Field(max_length=64)
    document_refs: list[str] = Field(default_factory=list)
    status: ParentLinkRequestStatus = ParentLinkRequestStatus.PENDING_VERIFICATION
    verification_method: ParentVerificationMethod | None = None
    review_notes: str | None = None
    reviewed_by: PydanticObjectId | None = None
    decided_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_student_link_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("student_user_id", ASCENDING)],
                name="link_requests_by_pair",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)],
                name="link_requests_by_status",
            ),
        ]


class ParentStudentRelationship(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    relationship_type: ParentRelationshipType
    status: ParentRelationshipStatus = ParentRelationshipStatus.PENDING_VERIFICATION
    link_request_id: PydanticObjectId | None = None
    verified_at: datetime | None = None
    verified_by: PydanticObjectId | None = None
    verification_method: ParentVerificationMethod | None = None
    suspended_at: datetime | None = None
    revoked_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_student_relationships"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("student_user_id", ASCENDING)],
                unique=True,
                name="unique_parent_student_pair",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("status", ASCENDING)],
                name="relationships_by_parent",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("status", ASCENDING)],
                name="relationships_by_student",
            ),
        ]


class ParentRelationshipPermissions(Document):
    tenant_id: PydanticObjectId
    relationship_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    grants: dict[str, bool] = Field(default_factory=dict)
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_relationship_permissions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("relationship_id", ASCENDING)],
                unique=True,
                name="unique_permissions_per_relationship",
            ),
        ]


class ParentRelationshipVerificationHistory(Document):
    tenant_id: PydanticObjectId
    relationship_id: PydanticObjectId | None = None
    link_request_id: PydanticObjectId | None = None
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    method: ParentVerificationMethod
    decision: str = Field(max_length=32)
    decided_by: PydanticObjectId | None = None
    notes: str | None = Field(default=None, max_length=2000)
    document_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_relationship_verification_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="parent_verification_history",
            ),
        ]


class ParentRelationshipStatusHistory(Document):
    tenant_id: PydanticObjectId
    relationship_id: PydanticObjectId
    from_status: ParentRelationshipStatus | None = None
    to_status: ParentRelationshipStatus
    reason: str | None = Field(default=None, max_length=500)
    changed_by: PydanticObjectId | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_relationship_status_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("relationship_id", ASCENDING), ("created_at", DESCENDING)],
                name="relationship_status_history",
            ),
        ]


class ParentRelationshipDocument(Document):
    tenant_id: PydanticObjectId
    relationship_id: PydanticObjectId | None = None
    link_request_id: PydanticObjectId | None = None
    parent_user_id: PydanticObjectId
    file_ref: str
    document_type: str = Field(max_length=64)
    label: str | None = Field(default=None, max_length=120)
    uploaded_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_relationship_documents"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING)],
                name="parent_relationship_docs",
            ),
        ]


class ParentLinkReferenceHint(Document):
    """Short-lived resolution token after a parent supplies a student reference (minimal PII)."""

    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    token_hash: str
    expires_at: datetime
    consumed: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_link_reference_hints"
        indexes = [
            IndexModel([("token_hash", ASCENDING)], unique=True, name="unique_link_hint_token"),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, name="link_hint_ttl"),
        ]


class ParentAcademicEnquiry(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    relationship_id: PydanticObjectId
    category: str = Field(max_length=64)
    description: str = Field(max_length=4000)
    requested_fields: dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="submitted", max_length=32)
    response_notes: str | None = Field(default=None, max_length=4000)
    responded_by: PydanticObjectId | None = None
    responded_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_academic_enquiries"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("student_user_id", ASCENDING)],
                name="parent_academic_enquiries_by_student",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="parent_academic_enquiries_status"),
        ]


class ParentAttendanceEnquiry(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    relationship_id: PydanticObjectId
    category: str = Field(max_length=64)
    course_code: str | None = Field(default=None, max_length=32)
    section: str | None = Field(default=None, max_length=32)
    attendance_date: date | None = None
    period_label: str | None = Field(default=None, max_length=64)
    description: str = Field(max_length=4000)
    supporting_info: dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="submitted", max_length=32)
    assigned_team: str | None = Field(default=None, max_length=64)
    response_notes: str | None = Field(default=None, max_length=4000)
    responded_by: PydanticObjectId | None = None
    responded_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_attendance_enquiries"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("status", ASCENDING)],
                name="parent_attendance_enquiries_queue",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="parent_attendance_enquiries_parent",
            ),
        ]


class ParentAttendanceEnquiryHistory(Document):
    tenant_id: PydanticObjectId
    enquiry_id: PydanticObjectId
    from_status: str | None = None
    to_status: str
    note: str | None = Field(default=None, max_length=2000)
    changed_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_attendance_enquiry_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("enquiry_id", ASCENDING), ("created_at", DESCENDING)],
                name="parent_attendance_enquiry_history",
            ),
        ]


class ParentAttendanceAlert(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    alert_key: str = Field(max_length=200)
    academic_year_label: str
    semester_label: str
    course_code: str | None = None
    section: str | None = None
    severity: str = Field(max_length=16)
    title: str = Field(max_length=200)
    body: str = Field(max_length=2000)
    percentage: float | None = None
    min_required: float | None = None
    source_updated_at: datetime | None = None
    acknowledged_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_attendance_alerts"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("alert_key", ASCENDING)],
                unique=True,
                name="unique_parent_attendance_alert",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("acknowledged_at", ASCENDING)],
                name="parent_alerts_inbox",
            ),
        ]


class ParentAttendanceAlertAcknowledgement(Document):
    tenant_id: PydanticObjectId
    alert_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    acknowledged_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_attendance_alert_acknowledgements"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("alert_id", ASCENDING), ("parent_user_id", ASCENDING)],
                unique=True,
                name="unique_alert_ack",
            ),
        ]


class ParentExamNotification(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    notification_key: str = Field(max_length=200)
    category: str = Field(max_length=64)
    title: str = Field(max_length=200)
    body: str = Field(max_length=2000)
    read_at: datetime | None = None
    source_ref: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_exam_notifications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("notification_key", ASCENDING)],
                unique=True,
                name="unique_parent_exam_notification",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("read_at", ASCENDING)],
                name="parent_exam_notifications_inbox",
            ),
        ]


class ParentExamDocumentAccessHistory(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    document_type: str = Field(max_length=64)
    document_ref: str
    accessed_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_exam_document_access_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("accessed_at", DESCENDING)],
                name="parent_exam_doc_access",
            ),
        ]


class ParentPaymentInitiationRecord(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    relationship_id: PydanticObjectId
    transaction_id: str
    demand_id: str
    idempotency_key: str
    amount: float
    gateway: str
    status: str = Field(max_length=32)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_payment_initiation_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_parent_payment_idempotency",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="parent_payments_by_parent",
            ),
        ]


class ParentPaymentTransactionReference(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    transaction_id: str
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_payment_transaction_references"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("transaction_id", ASCENDING)],
                unique=True,
                name="unique_parent_tx_ref",
            ),
        ]


class ParentFinanceEnquiry(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    relationship_id: PydanticObjectId
    category: str = Field(max_length=64)
    transaction_id: str | None = None
    receipt_id: str | None = None
    description: str = Field(max_length=4000)
    status: str = Field(default="submitted", max_length=32)
    response_notes: str | None = None
    responded_by: PydanticObjectId | None = None
    responded_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_finance_enquiries"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="parent_finance_enquiries_parent",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="parent_finance_enquiries_status"),
        ]


class ParentFinanceEnquiryHistory(Document):
    tenant_id: PydanticObjectId
    enquiry_id: PydanticObjectId
    from_status: str | None = None
    to_status: str
    note: str | None = Field(default=None, max_length=2000)
    changed_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_finance_enquiry_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("enquiry_id", ASCENDING), ("created_at", DESCENDING)],
                name="parent_finance_enquiry_history",
            ),
        ]


class ParentDeactivationRequest(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    reason: str | None = Field(default=None, max_length=1000)
    status: str = Field(default="pending", max_length=32)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_deactivation_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING)],
                name="parent_deactivation",
            ),
        ]


class ParentNotificationPreferences(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    in_app_enabled: bool = True
    preferred_language: str | None = Field(default=None, max_length=16)
    category_enabled: dict[str, bool] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_notification_preferences"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING)],
                unique=True,
                name="unique_parent_notification_prefs",
            ),
        ]


class ParentNotificationReadHistory(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    notification_key: str = Field(max_length=220)
    category: str = Field(max_length=64)
    student_user_id: PydanticObjectId | None = None
    source: str | None = Field(default=None, max_length=64)
    read_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_notification_read_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("notification_key", ASCENDING)],
                unique=True,
                name="unique_parent_notification_read",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("read_at", DESCENDING)],
                name="parent_notification_read_inbox",
            ),
        ]


class ParentNotificationAcknowledgement(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    notification_key: str = Field(max_length=220)
    student_user_id: PydanticObjectId | None = None
    requires_acknowledgement: bool = True
    acknowledged_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_notification_acknowledgements"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("notification_key", ASCENDING)],
                unique=True,
                name="unique_parent_notification_ack",
            ),
        ]


class ParentDocumentAccessRequest(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    relationship_id: PydanticObjectId
    document_category: str = Field(max_length=64)
    document_type: str = Field(max_length=64)
    academic_year_label: str | None = None
    semester_label: str | None = None
    reason: str = Field(max_length=2000)
    status: str = Field(default="submitted", max_length=32)
    response_notes: str | None = None
    fulfilled_document_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_document_access_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="parent_document_access_requests",
            ),
        ]


class ParentDocumentAccessHistory(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    document_id: str = Field(max_length=120)
    document_category: str = Field(max_length=64)
    document_type: str = Field(max_length=64)
    accessed_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_document_access_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("accessed_at", DESCENDING)],
                name="parent_document_access_history",
            ),
        ]


class ParentStudentServiceRequest(Document):
    tenant_id: PydanticObjectId
    request_id: str = Field(max_length=64)
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    relationship_id: PydanticObjectId
    category: str = Field(max_length=64)
    request_type: str = Field(max_length=64)
    subject: str = Field(max_length=200)
    description: str = Field(max_length=8000)
    priority: str = Field(default="normal", max_length=16)
    status: str = Field(default="submitted", max_length=32)
    assigned_team: str | None = None
    supporting_document_refs: list[str] = Field(default_factory=list)
    resolution_remarks: str | None = Field(default=None, max_length=4000)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_student_service_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("request_id", ASCENDING)],
                unique=True,
                name="unique_parent_service_request",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="parent_service_requests_parent",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="parent_service_requests_status"),
        ]


class ParentServiceRequestAssignment(Document):
    tenant_id: PydanticObjectId
    request_id: str = Field(max_length=64)
    service_request_id: PydanticObjectId
    assigned_team: str = Field(max_length=120)
    assigned_by: PydanticObjectId | None = None
    assigned_at: datetime = Field(default_factory=utcnow)
    notes: str | None = Field(default=None, max_length=2000)

    class Settings:
        name = "parent_service_request_assignments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("service_request_id", ASCENDING), ("assigned_at", DESCENDING)],
                name="parent_service_request_assignments",
            ),
        ]


class ParentServiceRequestComment(Document):
    tenant_id: PydanticObjectId
    service_request_id: PydanticObjectId
    request_id: str = Field(max_length=64)
    author_user_id: PydanticObjectId
    author_role: str = Field(max_length=32)
    body: str = Field(max_length=4000)
    attachment_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_service_request_comments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("service_request_id", ASCENDING), ("created_at", ASCENDING)],
                name="parent_service_request_comments",
            ),
        ]


class ParentServiceRequestHistory(Document):
    tenant_id: PydanticObjectId
    service_request_id: PydanticObjectId
    request_id: str = Field(max_length=64)
    from_status: str | None = None
    to_status: str
    note: str | None = Field(default=None, max_length=2000)
    changed_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_service_request_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("service_request_id", ASCENDING), ("created_at", DESCENDING)],
                name="parent_service_request_history",
            ),
        ]


class ParentSupportEnquiry(Document):
    tenant_id: PydanticObjectId
    enquiry_id: str = Field(max_length=64)
    parent_user_id: PydanticObjectId
    category: str = Field(max_length=64)
    subject: str = Field(max_length=200)
    description: str = Field(max_length=8000)
    status: str = Field(default="submitted", max_length=32)
    helpdesk_ticket_id: str | None = None
    response_notes: str | None = None
    responded_by: PydanticObjectId | None = None
    responded_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_support_enquiries"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("enquiry_id", ASCENDING)],
                unique=True,
                name="unique_parent_support_enquiry",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="parent_support_enquiries_parent",
            ),
        ]


class ParentMeetingCategory(Document):
    tenant_id: PydanticObjectId
    category_code: str = Field(max_length=64)
    title: str = Field(max_length=200)
    active: bool = True
    requires_staff_selection: bool = False
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_meeting_categories"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("category_code", ASCENDING)],
                unique=True,
                name="unique_parent_meeting_category",
            ),
        ]


class ParentMeetingAvailabilityPolicy(Document):
    tenant_id: PydanticObjectId
    policy_id: str = Field(default="default", max_length=32)
    weekdays: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4])
    day_start: str = Field(default="10:00", max_length=8)
    day_end: str = Field(default="16:00", max_length=8)
    slot_minutes: int = Field(default=30, ge=15, le=120)
    meeting_modes: list[str] = Field(default_factory=lambda: ["in_person", "online", "phone"])
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_meeting_availability"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("policy_id", ASCENDING)],
                unique=True,
                name="unique_parent_meeting_availability",
            ),
        ]


class ParentMeetingRequest(Document):
    tenant_id: PydanticObjectId
    request_id: str = Field(max_length=64)
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    relationship_id: PydanticObjectId
    category_code: str = Field(max_length=64)
    department_id: PydanticObjectId | None = None
    staff_user_id: PydanticObjectId | None = None
    purpose: str = Field(max_length=2000)
    remarks: str | None = Field(default=None, max_length=2000)
    preferred_date: date
    preferred_start: datetime
    preferred_end: datetime
    alternate_preferences: list[dict[str, Any]] = Field(default_factory=list)
    meeting_mode: str = Field(max_length=16)
    supporting_document_refs: list[str] = Field(default_factory=list)
    status: str = Field(default="submitted", max_length=32)
    rejection_reason: str | None = None
    appointment_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_meeting_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("request_id", ASCENDING)],
                unique=True,
                name="unique_parent_meeting_request",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="parent_meeting_requests_parent",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="parent_meeting_requests_status"),
        ]


class ParentMeetingAppointment(Document):
    tenant_id: PydanticObjectId
    appointment_id: str = Field(max_length=64)
    request_id: str = Field(max_length=64)
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    staff_user_id: PydanticObjectId | None = None
    department_id: PydanticObjectId | None = None
    category_code: str = Field(max_length=64)
    scheduled_start: datetime
    scheduled_end: datetime
    meeting_mode: str = Field(max_length=16)
    venue_or_link: str | None = Field(default=None, max_length=500)
    parent_visible_agenda: str | None = Field(default=None, max_length=4000)
    staff_preparation_notes: str | None = Field(default=None, max_length=4000)
    status: str = Field(default="scheduled", max_length=32)
    cancellation_reason: str | None = None
    cancelled_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_meeting_appointments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("appointment_id", ASCENDING)],
                unique=True,
                name="unique_parent_meeting_appointment",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("staff_user_id", ASCENDING), ("scheduled_start", ASCENDING)],
                name="parent_meeting_staff_schedule",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("scheduled_start", DESCENDING)],
                name="parent_meeting_parent_schedule",
            ),
        ]


class ParentMeetingHistory(Document):
    tenant_id: PydanticObjectId
    request_id: str = Field(max_length=64)
    appointment_id: str | None = None
    from_status: str | None = None
    to_status: str
    note: str | None = Field(default=None, max_length=2000)
    changed_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_meeting_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("request_id", ASCENDING), ("created_at", DESCENDING)],
                name="parent_meeting_history",
            ),
        ]


class ParentMeetingOutcome(Document):
    tenant_id: PydanticObjectId
    appointment_id: str = Field(max_length=64)
    parent_visible_summary: str = Field(max_length=4000)
    agreed_next_steps: str | None = Field(default=None, max_length=2000)
    staff_internal_notes: str | None = Field(default=None, max_length=4000)
    recorded_by: PydanticObjectId | None = None
    completed_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_meeting_outcomes"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("appointment_id", ASCENDING)],
                unique=True,
                name="unique_parent_meeting_outcome",
            ),
        ]


class ParentMeetingFollowup(Document):
    tenant_id: PydanticObjectId
    appointment_id: str = Field(max_length=64)
    followup_id: str = Field(max_length=64)
    description: str = Field(max_length=2000)
    responsible_person: str | None = Field(default=None, max_length=120)
    target_date: date | None = None
    status: str = Field(default="open", max_length=32)
    parent_visible: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_meeting_followups"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("appointment_id", ASCENDING)],
                name="parent_meeting_followups",
            ),
        ]


class ParentStudentServiceEnquiry(Document):
    tenant_id: PydanticObjectId
    enquiry_id: str = Field(max_length=64)
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId
    relationship_id: PydanticObjectId
    service_type: str = Field(max_length=32)
    subject: str = Field(max_length=200)
    description: str = Field(max_length=4000)
    status: str = Field(default="submitted", max_length=32)
    response_notes: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_student_service_enquiries"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("enquiry_id", ASCENDING)],
                unique=True,
                name="unique_parent_student_service_enquiry",
            ),
        ]


class ParentStudentServiceEnquiryHistory(Document):
    tenant_id: PydanticObjectId
    enquiry_id: str = Field(max_length=64)
    from_status: str | None = None
    to_status: str
    note: str | None = None
    changed_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_student_service_enquiry_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("enquiry_id", ASCENDING), ("created_at", DESCENDING)],
                name="parent_student_service_enquiry_history",
            ),
        ]


class ParentReportAccessHistory(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    student_user_id: PydanticObjectId | None = None
    report_category: str = Field(max_length=64)
    export_format: str = Field(default="json", max_length=16)
    filter_summary: dict[str, Any] = Field(default_factory=dict)
    accessed_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_report_access_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("accessed_at", DESCENDING)],
                name="parent_report_access_history",
            ),
        ]


class ParentAccountContactChangeRequest(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    channel: str = Field(max_length=16)
    proposed_value: str = Field(max_length=254)
    status: str = Field(default="pending", max_length=32)
    verification_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_account_contact_change_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="parent_contact_change_requests",
            ),
        ]


class ParentRelationshipAccessReviewRequest(Document):
    tenant_id: PydanticObjectId
    parent_user_id: PydanticObjectId
    relationship_id: PydanticObjectId
    student_user_id: PydanticObjectId
    action: str = Field(max_length=32)
    reason: str = Field(max_length=2000)
    status: str = Field(default="submitted", max_length=32)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "parent_relationship_access_review_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("parent_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="parent_relationship_review_requests",
            ),
        ]