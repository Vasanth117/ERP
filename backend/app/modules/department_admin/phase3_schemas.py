"""Department Admin phase 3 schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.department_admin.models import (
    DepartmentBatchStatus,
    DepartmentRequestStatus,
    DepartmentSectionStatus,
    DepartmentStudentFollowUpStatus,
    SectionTransferApprovalRecord,
    SectionTransferScenario,
)


class BatchCreate(BaseModel):
    programme_code: str = Field(min_length=2, max_length=32)
    batch_label: str = Field(min_length=2, max_length=64)
    admission_year: str | None = Field(default=None, max_length=16)
    expected_completion_year: str | None = Field(default=None, max_length=16)
    curriculum_version: str | None = Field(default=None, max_length=32)
    academic_year_label: str | None = Field(default=None, max_length=32)
    status: DepartmentBatchStatus | None = None


class BatchUpdate(BaseModel):
    admission_year: str | None = None
    expected_completion_year: str | None = None
    curriculum_version: str | None = None
    academic_year_label: str | None = None
    status: DepartmentBatchStatus | None = None


class BatchRead(BaseModel):
    batch_id: str
    programme_code: str
    batch_label: str
    admission_year: str | None
    expected_completion_year: str | None
    curriculum_version: str | None
    academic_year_label: str | None
    status: DepartmentBatchStatus
    student_count: int = 0
    section_count: int = 0
    updated_at: datetime


class SectionCreate(BaseModel):
    section_code: str = Field(min_length=1, max_length=16)
    name: str = Field(min_length=1, max_length=120)
    capacity: int = Field(default=60, ge=1, le=500)
    coordinator_user_id: str | None = None
    status: DepartmentSectionStatus | None = None


class SectionUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    capacity: int | None = Field(default=None, ge=1, le=500)
    coordinator_user_id: str | None = None
    status: DepartmentSectionStatus | None = None


class SectionRead(BaseModel):
    section_id: str
    batch_id: str
    section_code: str
    name: str
    capacity: int
    enrolled_count: int
    capacity_available: int
    coordinator_user_id: str | None
    status: DepartmentSectionStatus
    over_capacity: bool


class ClassStructureNode(BaseModel):
    programme_code: str
    batch_label: str
    batch_status: DepartmentBatchStatus
    sections: list[SectionRead]
    offerings_count: int = 0
    faculty_assignments_count: int = 0


class ClassStrengthSummary(BaseModel):
    programme_code: str
    batch_label: str
    section_code: str | None
    enrolled: int
    capacity: int | None
    unallocated_in_batch: int


class SectionTransferCreate(BaseModel):
    student_user_id: str
    from_section_code: str
    to_section_code: str
    batch_label: str
    to_batch_label: str | None = None
    programme_code: str
    to_programme_code: str | None = None
    destination_department_id: str | None = None
    effective_date: date | None = None
    reason: str = Field(min_length=3, max_length=1000)
    idempotency_key: str | None = Field(default=None, max_length=64)


class SectionTransferRead(BaseModel):
    request_id: str
    student_user_id: str
    from_section_code: str
    to_section_code: str
    from_batch_label: str
    to_batch_label: str
    batch_label: str
    programme_code: str
    transfer_scenario: SectionTransferScenario
    approval_steps: list[SectionTransferApprovalRecord]
    status: DepartmentRequestStatus
    effective_date: date | None
    reason: str
    created_at: datetime


class SectionTransferReview(BaseModel):
    decision: str = Field(pattern="^(approve|reject)$")
    rejection_reason: str | None = Field(default=None, max_length=500)


class StudentDirectoryFilters(BaseModel):
    programme_code: str | None = None
    batch_label: str | None = None
    section_code: str | None = None
    semester_label: str | None = None
    enrollment_status: str | None = None
    search: str | None = Field(default=None, max_length=120)


class StudentDirectoryItem(BaseModel):
    student_user_id: str
    full_name: str
    email: str
    roll_number: str | None
    programme_code: str | None
    batch_label: str | None
    section_code: str | None
    enrollment_status: str
    lifecycle_status: str


class StudentAcademicProfileRead(BaseModel):
    student_user_id: str
    roll_number: str | None
    programme_code: str | None
    batch_label: str | None
    section_code: str | None
    academic_year_label: str | None
    semester_label: str | None
    enrollment_lines: int
    academic_standing: str | None
    attendance_sessions_recorded: int | None = None


class EnrollmentSummaryRead(BaseModel):
    active: int
    withdrawn: int
    on_leave: int
    unallocated_section: int


class StudentCorrectionCreate(BaseModel):
    student_user_id: str
    field_name: str = Field(min_length=2, max_length=64)
    proposed_value: str = Field(min_length=1, max_length=500)
    reason: str = Field(min_length=3, max_length=2000)
    evidence_ref: str | None = None
    idempotency_key: str | None = Field(default=None, max_length=64)


class StudentCorrectionRead(BaseModel):
    request_id: str
    student_user_id: str
    field_name: str
    current_value: str | None
    proposed_value: str
    status: DepartmentRequestStatus
    reason: str
    created_at: datetime


class StudentCorrectionReview(BaseModel):
    decision: str = Field(pattern="^(approve|reject)$")
    decision_reason: str | None = Field(default=None, max_length=500)


class StudentFollowUpCreate(BaseModel):
    student_user_id: str
    category: str = Field(min_length=2, max_length=64)
    description: str = Field(min_length=3, max_length=2000)
    assigned_faculty_user_id: str | None = None
    due_date: date | None = None


class StudentFollowUpUpdate(BaseModel):
    status: DepartmentStudentFollowUpStatus | None = None
    resolution_notes: str | None = Field(default=None, max_length=2000)
    assigned_faculty_user_id: str | None = None
    due_date: date | None = None


class StudentFollowUpRead(BaseModel):
    follow_up_id: str
    student_user_id: str
    category: str
    description: str
    assigned_faculty_user_id: str | None
    due_date: date | None
    status: DepartmentStudentFollowUpStatus
    resolution_notes: str | None
    created_at: datetime