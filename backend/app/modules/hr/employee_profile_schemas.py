"""HR employee profile API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.common.roles import Role
from app.modules.college_admin.faculty_admin_models import FacultyEmploymentStatus
from app.modules.hr.employee_profile_models import EmergencyContact, HrEmployeeProfile, PostalAddress
from app.modules.hr.enums import ProfileCorrectionStatus, ProfileCompletionStatus, ProfileVerificationStatus


class EmergencyContactInput(EmergencyContact):
    pass


class PostalAddressInput(PostalAddress):
    pass


class EmployeeRegister(BaseModel):
    employee_code: str = Field(min_length=1, max_length=64)
    first_name: str = Field(min_length=1, max_length=120)
    middle_name: str | None = Field(default=None, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    official_email: EmailStr
    password: str | None = Field(default=None, min_length=8, max_length=128)
    link_existing_user_id: str | None = None
    institution_role: Role = Role.ACCOUNTS_STAFF
    personal_email: EmailStr | None = None
    mobile_number: str = Field(min_length=6, max_length=32)
    alternate_contact_number: str | None = Field(default=None, max_length=32)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=32)
    marital_status: str | None = None
    nationality: str | None = None
    profile_photo_file_id: str | None = None
    current_address: PostalAddressInput | None = None
    permanent_address: PostalAddressInput | None = None
    addresses_same: bool = False
    emergency_contact: EmergencyContactInput | None = None
    joining_date: date
    employee_category: str = Field(min_length=1, max_length=64)
    employment_type: str = Field(min_length=1, max_length=64)
    employment_status: FacultyEmploymentStatus = FacultyEmploymentStatus.PROBATION
    department_id: str
    designation: str = Field(min_length=1, max_length=120)
    campus_id: str | None = None
    reporting_manager_user_id: str | None = None
    probation_start_date: date | None = None
    probation_end_date: date | None = None
    contract_end_date: date | None = None


class EmployeeProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=120)
    middle_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    personal_email: EmailStr | None = None
    mobile_number: str | None = Field(default=None, max_length=32)
    alternate_contact_number: str | None = Field(default=None, max_length=32)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=32)
    marital_status: str | None = None
    nationality: str | None = None
    profile_photo_file_id: str | None = None
    current_address: PostalAddressInput | None = None
    permanent_address: PostalAddressInput | None = None
    addresses_same: bool | None = None
    emergency_contact: EmergencyContactInput | None = None
    employee_category: str | None = Field(default=None, max_length=64)
    employment_type: str | None = Field(default=None, max_length=64)
    department_id: str | None = None
    designation: str | None = Field(default=None, max_length=120)
    campus_id: str | None = None
    reporting_manager_user_id: str | None = None
    probation_start_date: date | None = None
    probation_end_date: date | None = None
    confirmation_date: date | None = None
    contract_end_date: date | None = None
    change_reason: str | None = Field(default=None, max_length=2000)


class EmployeeSearchQuery(BaseModel):
    employee_code: str | None = None
    name: str | None = None
    official_email: str | None = None
    mobile_number: str | None = None
    department_id: str | None = None
    designation: str | None = None
    campus_id: str | None = None
    employment_type: str | None = None
    employment_status: FacultyEmploymentStatus | None = None
    joining_from: date | None = None
    joining_to: date | None = None
    probation_only: bool = False
    profile_completion_status: ProfileCompletionStatus | None = None
    profile_verification_status: ProfileVerificationStatus | None = None


class EmploymentSummaryRead(BaseModel):
    employment_status: FacultyEmploymentStatus
    employment_type: str | None
    employee_category: str | None
    joining_date: date | None
    confirmation_date: date | None
    probation_start_date: date | None
    probation_end_date: date | None
    department_id: str | None
    designation: str | None
    campus_id: str | None
    reporting_manager_user_id: str | None


class EmployeeProfileRead(BaseModel):
    profile_id: str
    user_id: str
    employee_record_id: str
    employee_code: str
    full_name: str
    official_email: str
    personal_email: str | None
    mobile_number: str
    profile_completion_status: ProfileCompletionStatus
    profile_verification_status: ProfileVerificationStatus
    missing_fields: list[str]
    verification_note: str | None
    employment: EmploymentSummaryRead
    personal: dict
    addresses: dict
    emergency_contact: EmergencyContact | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_parts(cls, profile: HrEmployeeProfile, employee, *, full_name: str | None = None) -> "EmployeeProfileRead":
        display = full_name or f"{profile.first_name} {profile.middle_name or ''} {profile.last_name}".strip()
        display = " ".join(display.split())
        return cls(
            profile_id=str(profile.id),
            user_id=str(profile.user_id),
            employee_record_id=str(profile.employee_record_id),
            employee_code=profile.employee_code,
            full_name=display,
            official_email=str(profile.official_email),
            personal_email=str(profile.personal_email) if profile.personal_email else None,
            mobile_number=profile.mobile_number,
            profile_completion_status=profile.profile_completion_status,
            profile_verification_status=profile.profile_verification_status,
            missing_fields=list(profile.missing_fields),
            verification_note=profile.verification_note,
            employment=EmploymentSummaryRead(
                employment_status=employee.employment_status,
                employment_type=employee.employment_type,
                employee_category=profile.employee_category,
                joining_date=employee.joining_date,
                confirmation_date=profile.confirmation_date,
                probation_start_date=profile.probation_start_date,
                probation_end_date=profile.probation_end_date,
                department_id=str(employee.department_id) if employee.department_id else None,
                designation=employee.designation,
                campus_id=str(employee.campus_id) if employee.campus_id else None,
                reporting_manager_user_id=str(profile.reporting_manager_user_id) if profile.reporting_manager_user_id else None,
            ),
            personal={
                "first_name": profile.first_name,
                "middle_name": profile.middle_name,
                "last_name": profile.last_name,
                "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
                "gender": profile.gender,
                "marital_status": profile.marital_status,
                "nationality": profile.nationality,
                "profile_photo_file_id": profile.profile_photo_file_id,
            },
            addresses={
                "current_address": profile.current_address.model_dump() if profile.current_address else None,
                "permanent_address": profile.permanent_address.model_dump() if profile.permanent_address else None,
                "addresses_same": profile.addresses_same,
            },
            emergency_contact=profile.emergency_contact,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )


class EmployeeListItem(BaseModel):
    profile_id: str
    user_id: str
    employee_code: str
    full_name: str
    official_email: str
    department_id: str | None
    designation: str | None
    employment_status: FacultyEmploymentStatus
    profile_completion_status: ProfileCompletionStatus
    profile_verification_status: ProfileVerificationStatus


class ProfileVerificationDecision(BaseModel):
    decision: ProfileVerificationStatus
    note: str | None = Field(default=None, max_length=2000)


class EmploymentStatusChange(BaseModel):
    new_status: FacultyEmploymentStatus
    reason: str = Field(min_length=3, max_length=2000)
    effective_date: date | None = None


class ProfileCorrectionSubmit(BaseModel):
    proposed_changes: dict
    employee_note: str | None = Field(default=None, max_length=2000)


class ProfileCorrectionReview(BaseModel):
    decision: ProfileCorrectionStatus
    reviewer_note: str | None = Field(default=None, max_length=2000)


class ProfileChangeHistoryItem(BaseModel):
    field_group: str
    changes: dict
    previous_values: dict
    reason: str | None
    actor_id: str | None
    created_at: datetime


class ProfileCorrectionRead(BaseModel):
    correction_id: str
    employee_user_id: str
    proposed_changes: dict
    current_snapshot: dict
    employee_note: str | None
    status: ProfileCorrectionStatus
    reviewer_note: str | None
    created_at: datetime
    resolved_at: datetime | None