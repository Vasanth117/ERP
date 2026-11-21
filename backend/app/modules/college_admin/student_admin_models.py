"""College admin student lifecycle collections."""

from datetime import date, datetime
from enum import Enum

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.students.enums import StudentEnrollmentStatus


class AdmissionStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class StudentLifecycleStatus(str, Enum):
    ADMITTED = "admitted"
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    TRANSFERRED = "transferred"
    WITHDRAWN = "withdrawn"
    DISCONTINUED = "discontinued"
    GRADUATED = "graduated"


class TransferStatus(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class StudentAdmission(Document):
    tenant_id: PydanticObjectId
    admission_number: str = Field(min_length=4, max_length=32)
    applicant_name: str = Field(max_length=200)
    applicant_email: str = Field(max_length=254)
    programme_code: str
    department_id: PydanticObjectId | None = None
    batch_label: str | None = None
    academic_year_code: str
    status: AdmissionStatus = AdmissionStatus.PENDING
    confirmed_user_id: PydanticObjectId | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "student_admissions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("admission_number", ASCENDING)],
                unique=True,
                name="unique_admission_number",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="admissions_by_status"),
        ]


class StudentRecord(Document):
    """Authoritative institutional student record (syncs `student_profiles` + `users`)."""

    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    student_id: str | None = None
    roll_number: str | None = None
    admission_id: PydanticObjectId | None = None
    admission_number: str | None = None
    department_id: PydanticObjectId | None = None
    programme_code: str | None = None
    batch_label: str | None = None
    section_code: str | None = None
    lifecycle_status: StudentLifecycleStatus = StudentLifecycleStatus.ACTIVE
    enrollment_status: StudentEnrollmentStatus = StudentEnrollmentStatus.ACTIVE
    contact_phone: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "student_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_student_record_user",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("roll_number", ASCENDING)],
                unique=True,
                name="unique_student_roll",
                partialFilterExpression={"roll_number": {"$type": "string"}},
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_id", ASCENDING)],
                unique=True,
                name="unique_official_student_id",
                partialFilterExpression={"student_id": {"$type": "string"}},
            ),
        ]


class StudentStatusHistory(Document):
    tenant_id: PydanticObjectId
    student_record_id: PydanticObjectId
    user_id: PydanticObjectId
    from_status: str
    to_status: str
    reason: str | None = Field(default=None, max_length=500)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_status_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="student_status_history_user",
            ),
        ]


class StudentStatusChangeApproval(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class StudentWithdrawalType(str, Enum):
    WITHDRAWAL = "withdrawal"
    DISCONTINUATION = "discontinuation"


class StudentWithdrawalWorkflowStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class StudentWithdrawalRequest(Document):
    """Controlled student withdrawal or discontinuation workflow."""

    tenant_id: PydanticObjectId
    student_record_id: PydanticObjectId
    user_id: PydanticObjectId
    withdrawal_type: StudentWithdrawalType = StudentWithdrawalType.WITHDRAWAL
    last_attendance_date: date | None = None
    reason: str = Field(default="", max_length=500)
    workflow_status: StudentWithdrawalWorkflowStatus = StudentWithdrawalWorkflowStatus.DRAFT
    clearance_snapshots: dict[str, str] = Field(default_factory=dict)
    submitted_at: datetime | None = None
    approved_at: datetime | None = None
    approved_by: PydanticObjectId | None = None
    requested_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_withdrawal_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("workflow_status", ASCENDING), ("created_at", DESCENDING)],
                name="student_withdrawal_by_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_record_id", ASCENDING), ("created_at", DESCENDING)],
                name="student_withdrawal_by_record",
            ),
        ]


class StudentStatusChangeRequest(Document):
    """Queued student lifecycle status change awaiting college approval."""

    tenant_id: PydanticObjectId
    student_record_id: PydanticObjectId
    user_id: PydanticObjectId
    from_status_bucket: str = Field(max_length=32)
    from_status_label: str = Field(max_length=64)
    to_status_bucket: str = Field(max_length=32)
    to_status_label: str = Field(max_length=64)
    reason: str = Field(max_length=500)
    approval_status: StudentStatusChangeApproval = StudentStatusChangeApproval.PENDING
    requested_by: PydanticObjectId
    decided_by: PydanticObjectId | None = None
    decided_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_status_change_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("approval_status", ASCENDING), ("created_at", DESCENDING)],
                name="student_status_change_by_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_record_id", ASCENDING), ("created_at", DESCENDING)],
                name="student_status_change_by_record",
            ),
        ]


class StudentIdCardStatus(str, Enum):
    PENDING_PRINT = "pending_print"
    ACTIVE = "active"
    RENEWAL_DUE = "renewal_due"
    REPRINT_REQUESTED = "reprint_requested"
    BLOCKED = "blocked"


class StudentIdCard(Document):
    """Institutional student ID card issue and lifecycle."""

    tenant_id: PydanticObjectId
    student_record_id: PydanticObjectId
    user_id: PydanticObjectId
    card_number: str | None = Field(default=None, max_length=32)
    issued_at: datetime | None = None
    valid_until: date | None = None
    status: StudentIdCardStatus = StudentIdCardStatus.PENDING_PRINT
    reprint_reason: str | None = Field(default=None, max_length=120)
    blocked_reason: str | None = Field(default=None, max_length=200)
    print_batch_id: str | None = Field(default=None, max_length=64)
    issued_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_id_cards"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("student_record_id", ASCENDING)],
                unique=True,
                name="unique_student_id_card_record",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("status", ASCENDING), ("updated_at", DESCENDING)],
                name="student_id_card_by_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("card_number", ASCENDING)],
                unique=True,
                name="unique_student_card_number",
                partialFilterExpression={"card_number": {"$type": "string"}},
            ),
        ]


class StudentTransfer(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    from_department_id: PydanticObjectId | None = None
    to_department_id: PydanticObjectId | None = None
    from_programme_code: str | None = None
    to_programme_code: str | None = None
    reason: str = Field(max_length=1000)
    status: TransferStatus = TransferStatus.REQUESTED
    effective_date: date | None = None
    actor_id: PydanticObjectId | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None

    class Settings:
        name = "student_transfers"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)], name="transfers_by_user"),
        ]


class StudentPromotionRecord(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    from_academic_year: str
    from_semester: str
    to_academic_year: str
    to_semester: str
    decision: str = Field(max_length=64)
    cgpa_snapshot: float | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_promotion_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)], name="promotions_by_user"),
        ]


class StudentNewRegistrationDraft(Document):
    """Wizard draft for new student registration (CA 06.05)."""

    tenant_id: PydanticObjectId
    admission_id: PydanticObjectId
    actor_id: PydanticObjectId
    step_key: str = Field(default="student_information", max_length=48)
    values: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_new_registration_drafts"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("admission_id", ASCENDING)],
                unique=True,
                name="unique_registration_draft_per_admission",
            ),
        ]


class StudentGuardianRelationship(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    guardian_name: str = Field(max_length=120)
    relationship: str = Field(max_length=64)
    phone: str = Field(max_length=32)
    email: str | None = Field(default=None, max_length=254)
    portal_access_allowed: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_guardian_relationships"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("guardian_name", ASCENDING)],
                unique=True,
                name="unique_guardian_per_student",
            ),
        ]
