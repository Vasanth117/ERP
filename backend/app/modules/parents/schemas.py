"""Parent portal API schemas."""

from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.modules.parents.enums import (
    ParentAccountStatus,
    ParentDashboardDateRange,
    ParentLinkRequestStatus,
    ParentNotificationCategory,
    ParentRelationshipStatus,
    ParentRelationshipType,
    ParentVerificationMethod,
)
from app.modules.parents.models import (
    ParentAddress,
    ParentCommunicationPreferences,
    ParentProfile,
    ParentStudentLinkRequest,
    ParentStudentRelationship,
)


class ParentProfileRead(BaseModel):
    user_id: str
    email: str
    full_name: str
    display_name: str | None = None
    contact_phone: str | None = None
    alternate_email: str | None = None
    address: ParentAddress | None = None
    profile_photo_ref: str | None = None
    communication_preferences: ParentCommunicationPreferences
    account_status: ParentAccountStatus
    email_verified: bool
    mobile_verified: bool
    identity_verified: bool
    activated_at: datetime | None = None

    @classmethod
    def from_parts(cls, profile: ParentProfile, *, email: str, full_name: str) -> "ParentProfileRead":
        return cls(
            user_id=str(profile.user_id),
            email=email,
            full_name=full_name,
            display_name=profile.display_name or full_name,
            contact_phone=profile.contact_phone,
            alternate_email=profile.alternate_email,
            address=profile.address,
            profile_photo_ref=profile.profile_photo_ref,
            communication_preferences=profile.communication_preferences,
            account_status=profile.account_status,
            email_verified=profile.email_verified,
            mobile_verified=profile.mobile_verified,
            identity_verified=profile.identity_verified,
            activated_at=profile.activated_at,
        )


class ParentProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=200)
    contact_phone: str | None = Field(default=None, max_length=32)
    alternate_email: EmailStr | None = None
    address: ParentAddress | None = None
    profile_photo_ref: str | None = None
    communication_preferences: ParentCommunicationPreferences | None = None


class ParentCommunicationPreferencesUpdate(BaseModel):
    email_enabled: bool | None = None
    sms_enabled: bool | None = None
    push_enabled: bool | None = None
    preferred_language: str | None = Field(default=None, max_length=16)
    announcement_categories: list[str] | None = None


class ParentContactVerificationStart(BaseModel):
    channel: str = Field(pattern="^(email|mobile)$")
    target_value: str = Field(min_length=3, max_length=254)


class ParentContactVerificationConfirm(BaseModel):
    verification_id: str
    token: str = Field(min_length=4, max_length=64)


class ParentProfileCorrectionRequest(BaseModel):
    fields: dict[str, Any]
    reason: str | None = Field(default=None, max_length=1000)


class ParentDeactivationRequestInput(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


class StudentReferenceResolve(BaseModel):
    reference_type: str = Field(pattern="^(roll_number|student_id|admission_number)$")
    reference_value: str = Field(min_length=2, max_length=64)


class StudentReferencePreview(BaseModel):
    hint_token: str
    masked_display_name: str
    programme_hint: str | None = None
    batch_hint: str | None = None
    roll_suffix: str | None = None


class ParentLinkRequestCreate(BaseModel):
    hint_token: str
    relationship_type: ParentRelationshipType
    relationship_declaration: str = Field(min_length=10, max_length=2000)
    document_refs: list[str] = Field(default_factory=list)


class ParentLinkRequestRead(BaseModel):
    request_id: str
    student_user_id: str
    relationship_type: ParentRelationshipType
    status: ParentLinkRequestStatus
    review_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_doc(cls, doc: ParentStudentLinkRequest) -> "ParentLinkRequestRead":
        return cls(
            request_id=str(doc.id),
            student_user_id=str(doc.student_user_id),
            relationship_type=doc.relationship_type,
            status=doc.status,
            review_notes=doc.review_notes,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )


class ParentRelationshipRead(BaseModel):
    relationship_id: str
    student_user_id: str
    relationship_type: ParentRelationshipType
    status: ParentRelationshipStatus
    permissions: dict[str, bool] = Field(default_factory=dict)
    verified_at: datetime | None = None

    @classmethod
    def from_parts(
        cls,
        doc: ParentStudentRelationship,
        *,
        permissions: dict[str, bool] | None = None,
    ) -> "ParentRelationshipRead":
        return cls(
            relationship_id=str(doc.id),
            student_user_id=str(doc.student_user_id),
            relationship_type=doc.relationship_type,
            status=doc.status,
            permissions=permissions or {},
            verified_at=doc.verified_at,
        )


class LinkedStudentSummaryCard(BaseModel):
    student_user_id: str
    student_id: str | None = None
    roll_number: str | None = None
    full_name: str
    profile_photo_ref: str | None = None
    programme_code: str | None = None
    programme_name: str | None = None
    department_name: str | None = None
    batch_label: str | None = None
    semester_label: str | None = None
    academic_year_label: str | None = None
    enrollment_status: str | None = None
    attendance_summary: dict[str, Any] | None = None
    academic_performance_summary: dict[str, Any] | None = None
    upcoming_examinations: list[dict[str, Any]] = Field(default_factory=list)
    fee_summary: dict[str, Any] | None = None
    important_alerts: list[str] = Field(default_factory=list)
    pending_parent_actions: list[str] = Field(default_factory=list)


class ParentDashboardRead(BaseModel):
    parent: ParentProfileRead
    linked_student_count: int
    verified_linked_students: int
    pending_link_requests: int
    rejected_or_suspended_relationships: int
    selected_student_user_id: str | None = None
    student_summaries: list[LinkedStudentSummaryCard] = Field(default_factory=list)
    unread_notifications: int = 0
    announcements: list[dict[str, Any]] = Field(default_factory=list)
    academic_term: dict[str, str | None] = Field(default_factory=dict)
    filters_applied: dict[str, Any] = Field(default_factory=dict)


class ParentDashboardFilters(BaseModel):
    student_user_id: str | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None
    date_range: ParentDashboardDateRange = ParentDashboardDateRange.WEEK
    notification_category: ParentNotificationCategory | None = None
    request_status: str | None = None


class ParentLinkReviewDecision(BaseModel):
    decision: str = Field(pattern="^(approve|reject|request_info)$")
    verification_method: ParentVerificationMethod = ParentVerificationMethod.MANUAL_INSTITUTIONAL
    notes: str | None = Field(default=None, max_length=2000)
    permission_grants: dict[str, bool] | None = None


class ParentRelationshipAdminUpdate(BaseModel):
    status: ParentRelationshipStatus | None = None
    permission_grants: dict[str, bool] | None = None
    reason: str | None = Field(default=None, max_length=500)