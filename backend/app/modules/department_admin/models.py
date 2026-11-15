"""Department-owned configuration and workflow records (not duplicate master data)."""

from datetime import date, datetime, time
from enum import Enum

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class DepartmentProfileChangeStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class DepartmentProfileDetails(Document):
    """Extended profile fields editable by department admin (master row remains InstitutionDepartment)."""

    tenant_id: PydanticObjectId
    institution_department_id: PydanticObjectId
    central_department_id: PydanticObjectId
    description: str | None = Field(default=None, max_length=2000)
    contact_email: str | None = Field(default=None, max_length=254)
    contact_phone: str | None = Field(default=None, max_length=32)
    office_location: str | None = Field(default=None, max_length=500)
    website_url: str | None = Field(default=None, max_length=500)
    revision: int = 1
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "department_profile_details"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("institution_department_id", ASCENDING)],
                unique=True,
                name="unique_dept_profile_details",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING)],
                unique=True,
                name="unique_dept_profile_by_central",
            ),
        ]


class DepartmentSetting(Document):
    tenant_id: PydanticObjectId
    institution_department_id: PydanticObjectId
    setting_key: str = Field(min_length=2, max_length=64)
    setting_value: str | bool | int | float | list | dict
    category: str = "general"
    revision: int = 1
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "department_settings"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("institution_department_id", ASCENDING), ("setting_key", ASCENDING)],
                unique=True,
                name="unique_dept_setting_key",
            ),
        ]


class DepartmentSettingHistory(Document):
    tenant_id: PydanticObjectId
    institution_department_id: PydanticObjectId
    setting_key: str
    previous_value: str | bool | int | float | list | dict | None = None
    new_value: str | bool | int | float | list | dict | None = None
    changed_by: PydanticObjectId | None = None
    approval_reference_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_settings_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("institution_department_id", ASCENDING), ("created_at", DESCENDING)],
                name="dept_settings_history",
            ),
        ]


class DepartmentProfileChangeRequest(Document):
    tenant_id: PydanticObjectId
    institution_department_id: PydanticObjectId
    field_name: str = Field(min_length=2, max_length=64)
    previous_value: str | None = None
    proposed_value: str
    status: DepartmentProfileChangeStatus = DepartmentProfileChangeStatus.SUBMITTED
    requested_by: PydanticObjectId
    decided_by: PydanticObjectId | None = None
    decided_at: datetime | None = None
    rejection_reason: str | None = Field(default=None, max_length=500)
    idempotency_key: str | None = Field(default=None, max_length=64)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_profile_change_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("institution_department_id", ASCENDING), ("status", ASCENDING)],
                name="dept_change_by_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_dept_change_idempotency",
                partialFilterExpression={"idempotency_key": {"$type": "string"}},
            ),
        ]


class DepartmentRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class SectionTransferScenario(str, Enum):
    SAME_BATCH_SECTION = "same_batch_section"
    SAME_DEPT_INTER_BATCH = "same_dept_inter_batch"
    CROSS_DEPARTMENT = "cross_department"
    CROSS_COLLEGE = "cross_college"


class SectionTransferApprovalRole(str, Enum):
    SOURCE_DEPARTMENT_ADMIN = "source_department_admin"
    DESTINATION_DEPARTMENT_ADMIN = "destination_department_admin"
    COLLEGE_ADMIN = "college_admin"


class SectionTransferInitiator(str, Enum):
    STUDENT = "student"
    DEPARTMENT_ADMIN = "department_admin"


class SectionTransferApprovalRecord(BaseModel):
    role: SectionTransferApprovalRole
    status: DepartmentRequestStatus = DepartmentRequestStatus.PENDING
    decided_by: PydanticObjectId | None = None
    decided_at: datetime | None = None
    comment: str | None = Field(default=None, max_length=500)


class DepartmentBatchStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class DepartmentSectionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class DepartmentBatch(Document):
    tenant_id: PydanticObjectId
    institution_department_id: PydanticObjectId
    central_department_id: PydanticObjectId
    programme_code: str = Field(min_length=2, max_length=32)
    batch_label: str = Field(min_length=2, max_length=64)
    admission_year: str | None = Field(default=None, max_length=16)
    expected_completion_year: str | None = Field(default=None, max_length=16)
    curriculum_version: str | None = Field(default=None, max_length=32)
    academic_year_label: str | None = Field(default=None, max_length=32)
    status: DepartmentBatchStatus = DepartmentBatchStatus.DRAFT
    revision: int = 1
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "department_batches"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("central_department_id", ASCENDING),
                    ("programme_code", ASCENDING),
                    ("batch_label", ASCENDING),
                ],
                unique=True,
                name="unique_dept_batch",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="dept_batches_by_status"),
        ]


class DepartmentSection(Document):
    tenant_id: PydanticObjectId
    department_batch_id: PydanticObjectId
    central_department_id: PydanticObjectId
    section_code: str = Field(min_length=1, max_length=16)
    name: str = Field(min_length=1, max_length=120)
    capacity: int = Field(default=60, ge=1, le=500)
    coordinator_user_id: PydanticObjectId | None = None
    status: DepartmentSectionStatus = DepartmentSectionStatus.DRAFT
    revision: int = 1
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "department_sections"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("department_batch_id", ASCENDING), ("section_code", ASCENDING)],
                unique=True,
                name="unique_dept_section_per_batch",
            ),
            IndexModel([("tenant_id", ASCENDING), ("central_department_id", ASCENDING)], name="dept_sections_by_dept"),
        ]


class DepartmentSectionTransferRequest(Document):
    tenant_id: PydanticObjectId
    institution_department_id: PydanticObjectId
    central_department_id: PydanticObjectId
    destination_central_department_id: PydanticObjectId | None = None
    student_user_id: PydanticObjectId
    from_section_code: str
    to_section_code: str
    from_batch_label: str
    to_batch_label: str
    batch_label: str | None = Field(default=None, description="Deprecated mirror of from_batch_label")
    programme_code: str
    to_programme_code: str | None = None
    transfer_scenario: SectionTransferScenario = SectionTransferScenario.SAME_BATCH_SECTION
    initiator: SectionTransferInitiator = SectionTransferInitiator.DEPARTMENT_ADMIN
    effective_date: date | None = None
    reason: str = Field(max_length=1000)
    status: DepartmentRequestStatus = DepartmentRequestStatus.PENDING
    approval_steps: list[SectionTransferApprovalRecord] = Field(default_factory=list)
    requested_by: PydanticObjectId
    decided_by: PydanticObjectId | None = None
    decided_at: datetime | None = None
    rejection_reason: str | None = Field(default=None, max_length=500)
    idempotency_key: str | None = Field(default=None, max_length=64)
    execution_key: str | None = Field(default=None, max_length=64)
    student_record_updated_at: datetime | None = None
    destination_section_revision: int | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_section_transfer_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("status", ASCENDING)],
                name="dept_section_transfer_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_section_transfer_idem",
                partialFilterExpression={"idempotency_key": {"$type": "string"}},
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("execution_key", ASCENDING)],
                unique=True,
                name="unique_section_transfer_execution",
                partialFilterExpression={"execution_key": {"$type": "string"}},
            ),
        ]


class DepartmentSectionTransferHistory(Document):
    tenant_id: PydanticObjectId
    transfer_request_id: PydanticObjectId
    student_user_id: PydanticObjectId
    central_department_id: PydanticObjectId
    from_section_code: str
    to_section_code: str
    from_batch_label: str
    to_batch_label: str
    programme_code: str
    transfer_scenario: SectionTransferScenario
    effective_date: date | None = None
    completed_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_section_transfer_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="section_transfer_history_student",
            ),
        ]


class DepartmentStudentCorrectionRequest(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    student_user_id: PydanticObjectId
    field_name: str = Field(max_length=64)
    current_value: str | None = None
    proposed_value: str = Field(max_length=500)
    reason: str = Field(max_length=2000)
    evidence_ref: str | None = Field(default=None, max_length=256)
    status: DepartmentRequestStatus = DepartmentRequestStatus.PENDING
    requested_by: PydanticObjectId
    decided_by: PydanticObjectId | None = None
    decided_at: datetime | None = None
    decision_reason: str | None = Field(default=None, max_length=500)
    idempotency_key: str | None = Field(default=None, max_length=64)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_student_correction_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("status", ASCENDING)],
                name="dept_student_correction_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_dept_student_correction_idem",
                partialFilterExpression={"idempotency_key": {"$type": "string"}},
            ),
        ]


class DepartmentStudentFollowUpStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class DepartmentStudentFollowUp(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    student_user_id: PydanticObjectId
    category: str = Field(max_length=64)
    description: str = Field(max_length=2000)
    assigned_faculty_user_id: PydanticObjectId | None = None
    due_date: date | None = None
    status: DepartmentStudentFollowUpStatus = DepartmentStudentFollowUpStatus.OPEN
    resolution_notes: str | None = Field(default=None, max_length=2000)
    created_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_student_follow_ups"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("status", ASCENDING)],
                name="dept_followup_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("due_date", ASCENDING)],
                name="dept_followup_by_student_due",
            ),
        ]


class DepartmentFacultyAssignmentRequest(Document):
    """Request to assign or transfer faculty; does not change HR primary department until college approval."""

    tenant_id: PydanticObjectId
    institution_department_id: PydanticObjectId
    central_department_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    request_type: str = Field(description="assign|transfer")
    target_department_id: PydanticObjectId | None = None
    note: str | None = Field(default=None, max_length=1000)
    status: DepartmentRequestStatus = DepartmentRequestStatus.PENDING
    requested_by: PydanticObjectId
    idempotency_key: str | None = Field(default=None, max_length=64)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_faculty_assignment_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("status", ASCENDING)],
                name="dept_faculty_assign_req_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_dept_faculty_assign_idem",
                partialFilterExpression={"idempotency_key": {"$type": "string"}},
            ),
        ]


class DepartmentSubstituteRequest(Document):
    tenant_id: PydanticObjectId
    institution_department_id: PydanticObjectId
    central_department_id: PydanticObjectId
    original_faculty_user_id: PydanticObjectId
    substitute_faculty_user_id: PydanticObjectId | None = None
    course_code: str
    section: str
    academic_year_label: str
    semester_label: str
    session_date: date | None = None
    reason: str = Field(max_length=1000)
    status: DepartmentRequestStatus = DepartmentRequestStatus.PENDING
    requested_by: PydanticObjectId
    faculty_assignment_id: PydanticObjectId | None = None
    idempotency_key: str | None = Field(default=None, max_length=64)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_substitute_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("status", ASCENDING)],
                name="dept_substitute_by_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_dept_substitute_idem",
                partialFilterExpression={"idempotency_key": {"$type": "string"}},
            ),
        ]


class DepartmentTimetableStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class DepartmentTimetablePlan(Document):
    tenant_id: PydanticObjectId
    institution_department_id: PydanticObjectId
    central_department_id: PydanticObjectId
    academic_year_label: str
    semester_label: str
    programme_code: str | None = None
    batch_label: str | None = None
    title: str = Field(max_length=200)
    status: DepartmentTimetableStatus = DepartmentTimetableStatus.DRAFT
    revision: int = 1
    published_version: int = 0
    publish_idempotency_key: str | None = Field(default=None, max_length=64)
    created_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "department_timetable_plans"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("central_department_id", ASCENDING),
                    ("academic_year_label", ASCENDING),
                    ("semester_label", ASCENDING),
                    ("status", ASCENDING),
                ],
                name="dept_timetable_plans_term",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("publish_idempotency_key", ASCENDING)],
                unique=True,
                name="unique_dept_timetable_publish",
                partialFilterExpression={"publish_idempotency_key": {"$type": "string"}},
            ),
        ]


class DepartmentTimetableSlot(Document):
    plan_id: PydanticObjectId
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    programme_code: str | None = None
    batch_label: str | None = None
    section: str
    course_code: str
    course_name: str
    course_id: str | None = None
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    session_type: str = "lecture"
    room: str | None = None
    room_id: str | None = None
    laboratory: str | None = None
    revision: int = 1
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_timetable_slots"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("plan_id", ASCENDING), ("day_of_week", ASCENDING)], name="dept_slots_by_plan"),
            IndexModel(
                [("tenant_id", ASCENDING), ("plan_id", ASCENDING), ("faculty_user_id", ASCENDING), ("day_of_week", ASCENDING)],
                name="dept_slots_faculty_day",
            ),
        ]


class DepartmentTimetableChangeRequest(Document):
    tenant_id: PydanticObjectId
    plan_id: PydanticObjectId
    slot_id: PydanticObjectId | None = None
    change_type: str = Field(max_length=32)
    reason: str = Field(max_length=2000)
    previous_values: dict = Field(default_factory=dict)
    new_values: dict = Field(default_factory=dict)
    status: DepartmentRequestStatus = DepartmentRequestStatus.PENDING
    requested_by: PydanticObjectId
    decided_by: PydanticObjectId | None = None
    decided_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_timetable_change_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("plan_id", ASCENDING), ("status", ASCENDING)], name="dept_tt_change_status"),
        ]


class DepartmentTimetablePublishSnapshot(Document):
    tenant_id: PydanticObjectId
    plan_id: PydanticObjectId
    version: int
    slot_payloads: list[dict] = Field(default_factory=list)
    published_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_timetable_publish_snapshots"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("plan_id", ASCENDING), ("version", DESCENDING)], name="dept_tt_snapshots"),
        ]


class DepartmentExaminationIssueStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class DepartmentExaminationCoordinationIssue(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    issue_type: str = Field(max_length=64)
    severity: str = Field(default="warning", max_length=16)
    title: str = Field(max_length=200)
    description: str = Field(max_length=2000)
    references: dict = Field(default_factory=dict)
    assigned_faculty_user_id: PydanticObjectId | None = None
    due_date: date | None = None
    status: DepartmentExaminationIssueStatus = DepartmentExaminationIssueStatus.OPEN
    resolution_notes: str | None = Field(default=None, max_length=2000)
    idempotency_key: str | None = Field(default=None, max_length=128)
    created_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_examination_coordination_issues"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("status", ASCENDING)],
                name="dept_exam_issue_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("issue_type", ASCENDING)],
                name="dept_exam_issue_type",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_dept_exam_issue_idem",
                partialFilterExpression={"idempotency_key": {"$type": "string"}},
            ),
        ]


class DepartmentAttendanceDiscrepancy(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    discrepancy_type: str = Field(max_length=64)
    summary: str = Field(max_length=500)
    session_id: PydanticObjectId | None = None
    student_user_id: PydanticObjectId | None = None
    faculty_user_id: PydanticObjectId | None = None
    status: str = "open"
    detected_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_attendance_discrepancies"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("status", ASCENDING)],
                name="dept_attendance_discrepancy",
            ),
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("central_department_id", ASCENDING),
                    ("discrepancy_type", ASCENDING),
                    ("session_id", ASCENDING),
                ],
                unique=True,
                name="unique_dept_attendance_discrepancy_session",
                partialFilterExpression={"session_id": {"$type": "objectId"}},
            ),
        ]


class DepartmentCourseOfferingRequest(Document):
    """Proposed section offering; college admin publishes authoritative `section_offerings`."""

    tenant_id: PydanticObjectId
    institution_department_id: PydanticObjectId
    central_department_id: PydanticObjectId
    programme_code: str
    course_id: str
    course_code: str
    section_code: str
    batch_label: str | None = None
    academic_year_label: str
    semester_label: str
    faculty_user_id: PydanticObjectId | None = None
    status: DepartmentRequestStatus = DepartmentRequestStatus.PENDING
    requested_by: PydanticObjectId
    idempotency_key: str | None = Field(default=None, max_length=64)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_course_offering_requests"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("central_department_id", ASCENDING),
                    ("academic_year_label", ASCENDING),
                    ("semester_label", ASCENDING),
                ],
                name="dept_offering_req_term",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_dept_offering_idem",
                partialFilterExpression={"idempotency_key": {"$type": "string"}},
            ),
        ]


class DepartmentRequestCoordinationAction(str, Enum):
    REQUEST_INFORMATION = "request_information"
    FORWARD = "forward"
    ESCALATE = "escalate"
    CANCEL = "cancel"


class DepartmentRequestForwardTarget(str, Enum):
    COLLEGE_ADMIN = "college_admin"
    HR = "hr"
    EXAMINATION_CELL = "examination_cell"


class DepartmentRequestCoordinationRecord(BaseModel):
    action: DepartmentRequestCoordinationAction
    actor_user_id: PydanticObjectId
    comment: str | None = Field(default=None, max_length=2000)
    forward_target: DepartmentRequestForwardTarget | None = None
    previous_state: str | None = Field(default=None, max_length=64)
    new_state: str | None = Field(default=None, max_length=64)
    created_at: datetime = Field(default_factory=utcnow)


class DepartmentRequestCoordinationLog(Document):
    """Cross-cutting workflow actions; canonical request data stays in source collections."""

    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    request_category: str = Field(max_length=64)
    source_id: str = Field(max_length=64)
    records: list[DepartmentRequestCoordinationRecord] = Field(default_factory=list)
    assigned_reviewer_user_id: PydanticObjectId | None = None
    due_date: datetime | None = None
    escalation_level: int = 0
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_request_coordination_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("request_category", ASCENDING)],
                name="dept_req_coord_by_category",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("request_category", ASCENDING), ("source_id", ASCENDING)],
                unique=True,
                name="unique_dept_req_coord_source",
            ),
        ]


class DepartmentResourceType(str, Enum):
    CLASSROOM = "classroom"
    LABORATORY = "laboratory"
    EQUIPMENT = "equipment"
    TEACHING_MATERIAL = "teaching_material"
    PRACTICAL = "practical"


class DepartmentResourceRequest(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    resource_type: DepartmentResourceType
    resource_ref: str = Field(max_length=128)
    resource_name: str | None = Field(default=None, max_length=200)
    quantity: int = Field(default=1, ge=1, le=500)
    needed_from: datetime
    needed_until: datetime
    urgency: str = Field(default="normal", max_length=16)
    reason: str = Field(max_length=2000)
    status: DepartmentRequestStatus = DepartmentRequestStatus.PENDING
    requested_by: PydanticObjectId
    decided_by: PydanticObjectId | None = None
    decided_at: datetime | None = None
    decision_reason: str | None = Field(default=None, max_length=500)
    idempotency_key: str | None = Field(default=None, max_length=128)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_resource_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("status", ASCENDING)],
                name="dept_resource_req_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("resource_type", ASCENDING)],
                name="dept_resource_req_type",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_dept_resource_req_idem",
                partialFilterExpression={"idempotency_key": {"$type": "string"}},
            ),
        ]


class DepartmentResourceIssueStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class DepartmentResourceIssue(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    resource_type: DepartmentResourceType
    resource_ref: str = Field(max_length=128)
    issue_type: str = Field(max_length=64)
    description: str = Field(max_length=2000)
    status: DepartmentResourceIssueStatus = DepartmentResourceIssueStatus.OPEN
    reported_by: PydanticObjectId
    resolution_notes: str | None = Field(default=None, max_length=2000)
    idempotency_key: str | None = Field(default=None, max_length=128)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_resource_issues"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("status", ASCENDING)],
                name="dept_resource_issue_status",
            ),
        ]


class DepartmentReportJobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class DepartmentReportJob(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    requested_by: PydanticObjectId
    report_type: str = Field(max_length=64)
    filters: dict = Field(default_factory=dict)
    output_format: str = Field(default="json", max_length=16)
    status: DepartmentReportJobStatus = DepartmentReportJobStatus.PENDING
    row_count: int = 0
    result_preview: dict = Field(default_factory=dict)
    file_content_base64: str | None = None
    error_message: str | None = Field(default=None, max_length=2000)
    expires_at: datetime | None = None
    idempotency_key: str | None = Field(default=None, max_length=128)
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None

    class Settings:
        name = "department_report_jobs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("status", ASCENDING)],
                name="dept_report_job_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_dept_report_job_idem",
                partialFilterExpression={"idempotency_key": {"$type": "string"}},
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("requested_by", ASCENDING), ("created_at", DESCENDING)],
                name="dept_report_job_requester",
            ),
        ]


class DepartmentDataTransferOperation(str, Enum):
    IMPORT = "import"
    EXPORT = "export"


class DepartmentDataTransferStatus(str, Enum):
    UPLOADED = "uploaded"
    VALIDATED = "validated"
    VALIDATION_FAILED = "validation_failed"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class DepartmentDataTransferJob(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    requested_by: PydanticObjectId
    operation: DepartmentDataTransferOperation
    dataset_type: str = Field(max_length=64)
    template_version: str = Field(default="1", max_length=16)
    status: DepartmentDataTransferStatus = DepartmentDataTransferStatus.UPLOADED
    file_name: str | None = Field(default=None, max_length=256)
    file_content_base64: str | None = None
    validation_summary: dict = Field(default_factory=dict)
    row_errors: list[dict] = Field(default_factory=list)
    valid_row_count: int = 0
    invalid_row_count: int = 0
    executed_row_count: int = 0
    export_file_base64: str | None = None
    export_format: str | None = Field(default=None, max_length=16)
    error_message: str | None = Field(default=None, max_length=2000)
    expires_at: datetime | None = None
    idempotency_key: str | None = Field(default=None, max_length=128)
    dry_run: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None

    class Settings:
        name = "department_data_transfer_jobs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("operation", ASCENDING), ("status", ASCENDING)],
                name="dept_data_transfer_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_dept_data_transfer_idem",
                partialFilterExpression={"idempotency_key": {"$type": "string"}},
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("requested_by", ASCENDING), ("created_at", DESCENDING)],
                name="dept_data_transfer_requester",
            ),
        ]


class DepartmentEventStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


class DepartmentAnnouncementStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    EXPIRED = "expired"
    ARCHIVED = "archived"
    REJECTED = "rejected"


class DepartmentCalendarChangeRecord(BaseModel):
    changed_at: datetime = Field(default_factory=utcnow)
    changed_by: PydanticObjectId
    change_type: str = Field(max_length=32)
    reason: str | None = Field(default=None, max_length=500)
    before: dict = Field(default_factory=dict)
    after: dict = Field(default_factory=dict)


class DepartmentCalendarEvent(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    title: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    category: str = Field(max_length=64)
    starts_at: datetime
    ends_at: datetime
    timezone: str = Field(default="UTC", max_length=64)
    venue: str | None = Field(default=None, max_length=200)
    room: str | None = Field(default=None, max_length=64)
    laboratory: str | None = Field(default=None, max_length=64)
    organizer_user_id: PydanticObjectId
    responsible_faculty_user_id: PydanticObjectId | None = None
    audience_scope: str = Field(default="department", max_length=32)
    programme_code: str | None = Field(default=None, max_length=32)
    batch_label: str | None = Field(default=None, max_length=64)
    section_code: str | None = Field(default=None, max_length=16)
    visibility: str = Field(default="department_admin", max_length=32)
    academic_year_label: str | None = Field(default=None, max_length=32)
    semester_label: str | None = Field(default=None, max_length=32)
    related_course_code: str | None = Field(default=None, max_length=32)
    registration_required: bool = False
    status: DepartmentEventStatus = DepartmentEventStatus.DRAFT
    change_history: list[DepartmentCalendarChangeRecord] = Field(default_factory=list)
    idempotency_key: str | None = Field(default=None, max_length=128)
    created_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_calendar_events"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("starts_at", ASCENDING)],
                name="dept_calendar_by_start",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("status", ASCENDING)],
                name="dept_calendar_by_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("category", ASCENDING)],
                name="dept_calendar_by_category",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_dept_calendar_idem",
                partialFilterExpression={"idempotency_key": {"$type": "string"}},
            ),
        ]


class DepartmentAnnouncement(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    title: str = Field(max_length=200)
    body: str = Field(max_length=16000)
    category: str = Field(default="general", max_length=64)
    priority: str = Field(default="normal", max_length=16)
    audience_type: str = Field(max_length=32)
    programme_code: str | None = Field(default=None, max_length=32)
    batch_label: str | None = Field(default=None, max_length=64)
    section_code: str | None = Field(default=None, max_length=16)
    status: DepartmentAnnouncementStatus = DepartmentAnnouncementStatus.DRAFT
    author_user_id: PydanticObjectId
    publish_at: datetime | None = None
    expires_at: datetime | None = None
    scheduled_publish_at: datetime | None = None
    approved_by: PydanticObjectId | None = None
    approved_at: datetime | None = None
    approval_note: str | None = Field(default=None, max_length=500)
    rejection_reason: str | None = Field(default=None, max_length=500)
    attachment_refs: list[str] = Field(default_factory=list)
    delivery_summary: dict = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, max_length=128)
    publish_history: list[dict] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_announcements"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("status", ASCENDING)],
                name="dept_announcement_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("scheduled_publish_at", ASCENDING)],
                name="dept_announcement_schedule",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_dept_announcement_idem",
                partialFilterExpression={"idempotency_key": {"$type": "string"}},
            ),
        ]


class DepartmentAnnouncementAcknowledgement(Document):
    tenant_id: PydanticObjectId
    announcement_id: PydanticObjectId
    user_id: PydanticObjectId
    acknowledged_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_announcement_acknowledgements"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("announcement_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_dept_announcement_ack",
            ),
        ]


class DepartmentDocumentStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"
    PENDING_APPROVAL = "pending_approval"
    RESTRICTED = "restricted"
    DELETED = "deleted"


class DepartmentDocumentAccessScope(str, Enum):
    DEPT_ADMIN_ONLY = "dept_admin_only"
    DEPT_FACULTY = "dept_faculty"
    DEPT_STUDENTS = "dept_students"
    PROGRAMME = "programme"
    BATCH = "batch"
    SECTION = "section"
    EXPLICIT_USERS = "explicit_users"


class DepartmentDocument(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    title: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    category: str = Field(max_length=64)
    tags: list[str] = Field(default_factory=list)
    access_scope: DepartmentDocumentAccessScope = DepartmentDocumentAccessScope.DEPT_ADMIN_ONLY
    programme_code: str | None = Field(default=None, max_length=32)
    batch_label: str | None = Field(default=None, max_length=64)
    section_code: str | None = Field(default=None, max_length=16)
    authorized_user_ids: list[PydanticObjectId] = Field(default_factory=list)
    academic_year_label: str | None = Field(default=None, max_length=32)
    related_entity_type: str | None = Field(default=None, max_length=64)
    related_entity_id: str | None = Field(default=None, max_length=128)
    status: DepartmentDocumentStatus = DepartmentDocumentStatus.ACTIVE
    current_version: int = 1
    storage_key: str = Field(max_length=512)
    checksum: str = Field(max_length=128)
    file_name: str = Field(max_length=256)
    mime_type: str = Field(max_length=128)
    file_size: int = 0
    uploaded_by: PydanticObjectId
    idempotency_key: str | None = Field(default=None, max_length=128)
    retention_expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_documents"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("status", ASCENDING)],
                name="dept_doc_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("category", ASCENDING)],
                name="dept_doc_category",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("created_at", DESCENDING)],
                name="dept_doc_created",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_dept_doc_idem",
                partialFilterExpression={"idempotency_key": {"$type": "string"}},
            ),
        ]


class DepartmentDocumentVersion(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    document_id: PydanticObjectId
    version_number: int
    previous_version_id: PydanticObjectId | None = None
    storage_key: str = Field(max_length=512)
    checksum: str = Field(max_length=128)
    file_name: str = Field(max_length=256)
    mime_type: str = Field(max_length=128)
    file_size: int = 0
    uploaded_by: PydanticObjectId
    update_reason: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_document_versions"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("document_id", ASCENDING),
                    ("version_number", ASCENDING),
                ],
                unique=True,
                name="unique_dept_doc_version",
            ),
        ]


class DepartmentDocumentHistory(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    document_id: PydanticObjectId
    event_type: str = Field(max_length=64)
    actor_user_id: PydanticObjectId | None = None
    summary: str | None = Field(default=None, max_length=500)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_document_history"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("document_id", ASCENDING),
                    ("created_at", DESCENDING),
                ],
                name="dept_doc_history",
            ),
        ]


class DepartmentAuditExportJob(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    requested_by: PydanticObjectId
    filters: dict = Field(default_factory=dict)
    row_count: int = 0
    file_content_base64: str | None = None
    expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_audit_export_jobs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("created_at", DESCENDING)],
                name="dept_audit_export",
            ),
        ]


class DepartmentHelpdeskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class DepartmentHelpdeskStatus(str, Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_INFORMATION = "waiting_for_information"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class DepartmentHelpdeskEscalationTarget(str, Enum):
    COLLEGE_ADMIN = "college_admin"
    IT_SUPPORT = "it_support"
    HR = "hr"
    EXAMINATION_CELL = "examination_cell"
    FACILITIES = "facilities"
    PLATFORM_SUPPORT = "platform_support"


class DepartmentHelpdeskTicket(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    ticket_number: str = Field(max_length=32)
    title: str = Field(max_length=200)
    description: str = Field(max_length=8000)
    category: str = Field(max_length=64)
    priority: DepartmentHelpdeskPriority = DepartmentHelpdeskPriority.NORMAL
    affected_module: str | None = Field(default=None, max_length=64)
    affected_record_type: str | None = Field(default=None, max_length=64)
    affected_record_id: str | None = Field(default=None, max_length=128)
    requester_user_id: PydanticObjectId
    assigned_user_id: PydanticObjectId | None = None
    assigned_team: str | None = Field(default=None, max_length=64)
    status: DepartmentHelpdeskStatus = DepartmentHelpdeskStatus.OPEN
    escalation_target: DepartmentHelpdeskEscalationTarget | None = None
    escalation_note: str | None = Field(default=None, max_length=1000)
    document_ids: list[PydanticObjectId] = Field(default_factory=list)
    preferred_resolution_at: datetime | None = None
    first_response_due_at: datetime | None = None
    resolution_due_at: datetime | None = None
    resolved_at: datetime | None = None
    resolved_by: PydanticObjectId | None = None
    resolution_note: str | None = Field(default=None, max_length=4000)
    closed_at: datetime | None = None
    idempotency_key: str | None = Field(default=None, max_length=128)
    created_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_helpdesk_tickets"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("status", ASCENDING)],
                name="dept_helpdesk_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("priority", ASCENDING)],
                name="dept_helpdesk_priority",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("assigned_user_id", ASCENDING)],
                name="dept_helpdesk_assignee",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("ticket_number", ASCENDING)],
                unique=True,
                name="unique_dept_helpdesk_ticket_no",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_dept_helpdesk_idem",
                partialFilterExpression={"idempotency_key": {"$type": "string"}},
            ),
        ]


class DepartmentHelpdeskComment(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    ticket_id: PydanticObjectId
    body: str = Field(max_length=8000)
    is_internal: bool = False
    author_user_id: PydanticObjectId
    attachment_document_ids: list[PydanticObjectId] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_helpdesk_comments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("ticket_id", ASCENDING), ("created_at", ASCENDING)],
                name="dept_helpdesk_comments",
            ),
        ]


class DepartmentHelpdeskHistory(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    ticket_id: PydanticObjectId
    change_type: str = Field(max_length=32)
    actor_user_id: PydanticObjectId | None = None
    summary: str | None = Field(default=None, max_length=500)
    before: dict = Field(default_factory=dict)
    after: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_helpdesk_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("ticket_id", ASCENDING), ("created_at", DESCENDING)],
                name="dept_helpdesk_history",
            ),
        ]


class DepartmentPlacementActivityStatus(str, Enum):
    PLANNED = "planned"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DepartmentPlacementActivity(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    title: str = Field(max_length=200)
    activity_type: str = Field(max_length=64)
    description: str | None = Field(default=None, max_length=4000)
    academic_year_label: str | None = Field(default=None, max_length=32)
    programme_code: str | None = Field(default=None, max_length=32)
    batch_label: str | None = Field(default=None, max_length=64)
    scheduled_at: datetime | None = None
    status: DepartmentPlacementActivityStatus = DepartmentPlacementActivityStatus.PLANNED
    calendar_event_id: PydanticObjectId | None = None
    coordinator_user_id: PydanticObjectId
    participant_count: int = 0
    idempotency_key: str | None = Field(default=None, max_length=128)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_placement_activities"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("status", ASCENDING)],
                name="dept_placement_activity_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("scheduled_at", ASCENDING)],
                name="dept_placement_activity_schedule",
            ),
        ]


class DepartmentInternshipStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DepartmentInternshipCoordination(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    title: str = Field(max_length=200)
    organization_name: str = Field(max_length=200)
    organization_website: str | None = Field(default=None, max_length=256)
    organization_verified: bool = False
    student_user_id: PydanticObjectId
    faculty_coordinator_id: PydanticObjectId
    duration_label: str | None = Field(default=None, max_length=64)
    academic_year_label: str | None = Field(default=None, max_length=32)
    status: DepartmentInternshipStatus = DepartmentInternshipStatus.DRAFT
    document_ids: list[PydanticObjectId] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=2000)
    idempotency_key: str | None = Field(default=None, max_length=128)
    created_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_internship_coordinations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("status", ASCENDING)],
                name="dept_internship_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING)],
                name="dept_internship_student",
            ),
        ]


class DepartmentProjectCoordinationStatus(str, Enum):
    PROPOSED = "proposed"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DepartmentProjectCoordination(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    title: str = Field(max_length=200)
    project_type: str = Field(max_length=64)
    student_user_ids: list[PydanticObjectId] = Field(default_factory=list)
    faculty_guide_id: PydanticObjectId
    lms_assignment_id: PydanticObjectId | None = None
    academic_year_label: str | None = Field(default=None, max_length=32)
    programme_code: str | None = Field(default=None, max_length=32)
    milestones: list[dict] = Field(default_factory=list)
    status: DepartmentProjectCoordinationStatus = DepartmentProjectCoordinationStatus.PROPOSED
    submission_status: str | None = Field(default=None, max_length=64)
    document_ids: list[PydanticObjectId] = Field(default_factory=list)
    created_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_project_coordinations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("status", ASCENDING)],
                name="dept_project_coord_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_guide_id", ASCENDING)],
                name="dept_project_coord_faculty",
            ),
        ]


class DepartmentResearchProjectStatus(str, Enum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class DepartmentResearchProject(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    title: str = Field(max_length=200)
    faculty_lead_id: PydanticObjectId
    student_participant_ids: list[PydanticObjectId] = Field(default_factory=list)
    status: DepartmentResearchProjectStatus = DepartmentResearchProjectStatus.PROPOSED
    publication_refs: list[str] = Field(default_factory=list)
    seminar_scheduled_at: datetime | None = None
    document_ids: list[PydanticObjectId] = Field(default_factory=list)
    academic_year_label: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=4000)
    created_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_research_projects"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("central_department_id", ASCENDING), ("status", ASCENDING)],
                name="dept_research_project_status",
            ),
        ]


class DepartmentProjectReviewStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DepartmentProjectReview(Document):
    tenant_id: PydanticObjectId
    central_department_id: PydanticObjectId
    project_id: PydanticObjectId
    review_type: str = Field(max_length=64)
    milestone_label: str | None = Field(default=None, max_length=128)
    scheduled_at: datetime
    reviewer_faculty_ids: list[PydanticObjectId] = Field(default_factory=list)
    status: DepartmentProjectReviewStatus = DepartmentProjectReviewStatus.SCHEDULED
    feedback_ref: str | None = Field(default=None, max_length=512)
    calendar_event_id: PydanticObjectId | None = None
    created_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "department_project_reviews"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("project_id", ASCENDING), ("scheduled_at", ASCENDING)],
                name="dept_project_review_schedule",
            ),
        ]