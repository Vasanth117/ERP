"""HR employee profile extensions (authoritative personal data; links to EmployeeRecord)."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, EmailStr, Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import ProfileCorrectionStatus, ProfileCompletionStatus, ProfileVerificationStatus


class PostalAddress(BaseModel):
    line1: str = Field(max_length=300)
    line2: str | None = Field(default=None, max_length=300)
    city: str | None = Field(default=None, max_length=120)
    district: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=120)
    postal_code: str | None = Field(default=None, max_length=32)


class EmergencyContact(BaseModel):
    name: str = Field(max_length=200)
    relationship: str = Field(max_length=120)
    primary_phone: str = Field(max_length=32)
    alternate_phone: str | None = Field(default=None, max_length=32)
    address: str | None = Field(default=None, max_length=500)


class HrEmployeeProfile(Document):
    """Extended employee profile; employment row remains EmployeeRecord."""

    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    employee_record_id: PydanticObjectId
    employee_code: str = Field(max_length=64)
    first_name: str = Field(max_length=120)
    middle_name: str | None = Field(default=None, max_length=120)
    last_name: str = Field(max_length=120)
    profile_photo_file_id: str | None = None
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=32)
    personal_email: EmailStr | None = None
    official_email: EmailStr
    mobile_number: str = Field(max_length=32)
    alternate_contact_number: str | None = Field(default=None, max_length=32)
    marital_status: str | None = Field(default=None, max_length=64)
    nationality: str | None = Field(default=None, max_length=64)
    current_address: PostalAddress | None = None
    permanent_address: PostalAddress | None = None
    addresses_same: bool = False
    emergency_contact: EmergencyContact | None = None
    employee_category: str | None = Field(default=None, max_length=64)
    reporting_manager_user_id: PydanticObjectId | None = None
    probation_start_date: date | None = None
    probation_end_date: date | None = None
    confirmation_date: date | None = None
    contract_end_date: date | None = None
    profile_completion_status: ProfileCompletionStatus = ProfileCompletionStatus.INCOMPLETE
    profile_verification_status: ProfileVerificationStatus = ProfileVerificationStatus.PENDING_VERIFICATION
    verification_note: str | None = Field(default=None, max_length=2000)
    verified_by: PydanticObjectId | None = None
    verified_at: datetime | None = None
    missing_fields: list[str] = Field(default_factory=list)
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_employee_profiles"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_hr_profile_per_user",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_code", ASCENDING)],
                unique=True,
                name="unique_hr_employee_code",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("profile_verification_status", ASCENDING)],
                name="hr_profiles_by_verification",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("profile_completion_status", ASCENDING)],
                name="hr_profiles_by_completion",
            ),
        ]


class HrEmployeeProfileChangeLog(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    field_group: str = Field(max_length=64)
    changes: dict[str, Any] = Field(default_factory=dict)
    previous_values: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = Field(default=None, max_length=2000)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_employee_profile_change_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="hr_profile_changes_by_user",
            ),
        ]


class HrEmployeeProfileCorrectionRequest(Document):
    tenant_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    proposed_changes: dict[str, Any] = Field(default_factory=dict)
    current_snapshot: dict[str, Any] = Field(default_factory=dict)
    employee_note: str | None = Field(default=None, max_length=2000)
    status: ProfileCorrectionStatus = ProfileCorrectionStatus.SUBMITTED
    reviewer_id: PydanticObjectId | None = None
    reviewer_note: str | None = Field(default=None, max_length=2000)
    resolved_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_employee_profile_corrections"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("employee_user_id", ASCENDING), ("status", ASCENDING)],
                name="hr_corrections_by_user_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)],
                name="hr_corrections_pending",
            ),
        ]

