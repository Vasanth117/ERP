"""HR enumerations."""

from enum import Enum


class LeaveRequestStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_MANAGER = "pending_manager"
    PENDING_HR = "pending_hr"
    CLARIFICATION_REQUESTED = "clarification_requested"
    CANCEL_REQUESTED = "cancel_requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class LeaveDayPortion(str, Enum):
    FULL = "full"
    FIRST_HALF = "first_half"
    SECOND_HALF = "second_half"


class HrEmploymentChangeType(str, Enum):
    DEPARTMENT_TRANSFER = "department_transfer"
    SUB_DEPARTMENT_TRANSFER = "sub_department_transfer"
    DESIGNATION_CHANGE = "designation_change"
    PROMOTION = "promotion"
    DEMOTION = "demotion"
    REPORTING_MANAGER_CHANGE = "reporting_manager_change"
    CAMPUS_TRANSFER = "campus_transfer"
    WORK_LOCATION_CHANGE = "work_location_change"
    EMPLOYMENT_TYPE_CHANGE = "employment_type_change"
    EMPLOYMENT_CATEGORY_CHANGE = "employment_category_change"
    CONTRACT_EXTENSION = "contract_extension"
    CONTRACT_RENEWAL = "contract_renewal"
    PROBATION_EXTENSION = "probation_extension"
    PROBATION_CONFIRMATION = "probation_confirmation"
    EMPLOYMENT_STATUS_CHANGE = "employment_status_change"
    TEMPORARY_ASSIGNMENT = "temporary_assignment"
    SALARY_REVISION = "salary_revision"
    OTHER = "other"


class HrEmploymentChangeStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_MANAGER = "pending_manager"
    PENDING_HR = "pending_hr"
    PENDING_MANAGEMENT = "pending_management"
    RETURNED = "returned"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    APPLIED = "applied"
    CANCELLED = "cancelled"


class HrResignationStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    AWAITING_MANAGER_APPROVAL = "awaiting_manager_approval"
    AWAITING_HR_APPROVAL = "awaiting_hr_approval"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    NOTICE_PERIOD = "notice_period"
    EXIT_IN_PROGRESS = "exit_in_progress"
    COMPLETED = "completed"


class HrOffboardingProcessStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PENDING_CLEARANCE = "pending_clearance"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class HrOffboardingTaskStatus(str, Enum):
    NOT_STARTED = "not_started"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PENDING_CLEARANCE = "pending_clearance"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class HrProbationReviewStatus(str, Enum):
    DRAFT = "draft"
    PENDING_MANAGER = "pending_manager"
    PENDING_HR = "pending_hr"
    CONFIRMATION_RECOMMENDED = "confirmation_recommended"
    EXTENSION_RECOMMENDED = "extension_recommended"
    CONFIRMED = "confirmed"
    EXTENDED = "extended"
    REJECTED = "rejected"


class ProfileCompletionStatus(str, Enum):
    INCOMPLETE = "incomplete"
    COMPLETE = "complete"


class ProfileVerificationStatus(str, Enum):
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    REJECTED = "rejected"


class ProfileCorrectionStatus(str, Enum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class EmployeeAttendanceDayStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    ON_LEAVE = "on_leave"
    LATE = "late"
    EARLY_DEPARTURE = "early_departure"
    MISSING = "missing"
    HALF_DAY = "half_day"
    HOLIDAY = "holiday"
    WEEKLY_OFF = "weekly_off"
    WORK_FROM_HOME = "work_from_home"
    MISSING_PUNCH = "missing_punch"
    INCOMPLETE = "incomplete"


class EmployeeAttendanceCorrectionStatus(str, Enum):
    PENDING = "pending"
    PENDING_MANAGER = "pending_manager"
    PENDING_HR = "pending_hr"
    APPROVED = "approved"
    REJECTED = "rejected"


class HrShiftKind(str, Enum):
    GENERAL = "general"
    MORNING = "morning"
    EVENING = "evening"
    NIGHT = "night"
    ROTATIONAL = "rotational"
    CUSTOM = "custom"


class HrRosterAssignmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    SWAP_PENDING = "swap_pending"
    REPLACED = "replaced"
    CANCELLED = "cancelled"


class HrAttendanceEventSource(str, Enum):
    MANUAL_HR = "manual_hr"
    BIOMETRIC = "biometric"
    ATTENDANCE_MACHINE = "attendance_machine"
    EMPLOYEE_CHECKIN = "employee_checkin"
    IMPORT = "import"


class HrAttendanceEventType(str, Enum):
    CHECK_IN = "check_in"
    CHECK_OUT = "check_out"
    BREAK_START = "break_start"
    BREAK_END = "break_end"


class HrMonthlyAttendanceStatus(str, Enum):
    OPEN = "open"
    CLOSING = "closing"
    LOCKED = "locked"
    REOPENED = "reopened"


class HrSalaryComponentCategory(str, Enum):
    EARNING = "earning"
    DEDUCTION = "deduction"


class HrSalaryCalcType(str, Enum):
    FIXED = "fixed"
    PERCENTAGE = "percentage"


class HrSalaryTemplateStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class HrSalaryAssignmentStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    CANCELLED = "cancelled"


class HrSalaryRevisionStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    APPLIED = "applied"
    REJECTED = "rejected"


class HrRecruitmentApplicationStatus(str, Enum):
    """Legacy dashboard buckets; job applications use HrApplicationPipelineStage."""

    NEW = "new"
    UNDER_REVIEW = "under_review"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    AWAITING_FEEDBACK = "awaiting_feedback"
    SELECTED = "selected"
    REJECTED = "rejected"
    AWAITING_OFFER_ACCEPTANCE = "awaiting_offer_acceptance"


class HrApplicationPipelineStage(str, Enum):
    APPLICATION_SUBMITTED = "application_submitted"
    INITIAL_SCREENING = "initial_screening"
    UNDER_REVIEW = "under_review"
    SHORTLISTED = "shortlisted"
    ASSESSMENT = "assessment"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    FINAL_EVALUATION = "final_evaluation"
    SELECTED = "selected"
    OFFER_ISSUED = "offer_issued"
    OFFER_ACCEPTED = "offer_accepted"
    OFFER_DECLINED = "offer_declined"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    POSITION_CLOSED = "position_closed"


class HrJobRequisitionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    HR_REVIEW = "hr_review"
    PENDING_MANAGEMENT_APPROVAL = "pending_management_approval"
    RETURNED_FOR_CLARIFICATION = "returned_for_clarification"
    APPROVED = "approved"
    REJECTED = "rejected"


class HrJobOpeningStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    PAUSED = "paused"
    CLOSED_FILLED = "closed_filled"
    CLOSED_CANCELLED = "closed_cancelled"


class HrEmploymentOfferStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ISSUED = "issued"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class HrInterviewStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class HrOnboardingProcessStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PENDING_COMPLETION = "pending_completion"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class HrOnboardingTaskStatus(str, Enum):
    NOT_STARTED = "not_started"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PENDING_EMPLOYEE = "pending_employee"
    PENDING_HR = "pending_hr"
    PENDING_DEPARTMENT = "pending_department"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


TERMINAL_APPLICATION_STAGES = frozenset(
    {
        HrApplicationPipelineStage.REJECTED,
        HrApplicationPipelineStage.WITHDRAWN,
        HrApplicationPipelineStage.OFFER_ACCEPTED,
        HrApplicationPipelineStage.OFFER_DECLINED,
        HrApplicationPipelineStage.POSITION_CLOSED,
    }
)


class HrDocumentVerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class HrDashboardDateRange(str, Enum):
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    CUSTOM = "custom"


class HrPayrollRunStatus(str, Enum):
    DRAFT = "draft"
    CALCULATING = "calculating"
    VALIDATION_REQUIRED = "validation_required"
    READY_FOR_REVIEW = "ready_for_review"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PAYMENT_PROCESSING = "payment_processing"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REOPENED = "reopened"


class HrPayrollEmployeeStatus(str, Enum):
    ELIGIBLE = "eligible"
    EXCLUDED = "excluded"
    CALCULATED = "calculated"
    EXCEPTION = "exception"
    PAID = "paid"
    PAYMENT_FAILED = "payment_failed"


class HrPayslipStatus(str, Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    UNDER_REVIEW = "under_review"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"
    FAILED = "failed"


class HrStaffActivityType(str, Enum):
    EMPLOYEE_REGISTERED = "employee_registered"
    PROFILE_UPDATED = "profile_updated"
    DEPARTMENT_CHANGED = "department_changed"
    DESIGNATION_CHANGED = "designation_changed"
    STATUS_CHANGED = "status_changed"
    LEAVE_APPLICATION = "leave_application"
    ATTENDANCE_CORRECTION = "attendance_correction"
    RECRUITMENT_UPDATE = "recruitment_update"
    ONBOARDING_COMPLETED = "onboarding_completed"
    PAYROLL_ACTIVITY = "payroll_activity"
    EMPLOYEE_EXIT = "employee_exit"
    PROFILE_VERIFICATION = "profile_verification"
    PROFILE_CORRECTION = "profile_correction"
    POLICY_CHANGE = "policy_change"
    ACCESS_CHANGE = "access_change"


# Status changes that require an offboarding record (not a simple toggle).
OFFBOARDING_REQUIRED_STATUSES = frozenset({"resigned", "terminated"})


class HrEmploymentClassificationKind(str, Enum):
    TYPE = "employment_type"
    CATEGORY = "employment_category"


class HrWorkLocationStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class HrEmployeeTransferStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    APPLIED = "applied"
    CANCELLED = "cancelled"


class HrEmployeeDocumentStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REPLACED = "replaced"
    ARCHIVED = "archived"


class HrStatutoryComponentKind(str, Enum):
    EMPLOYEE_DEDUCTION = "employee_deduction"
    EMPLOYER_CONTRIBUTION = "employer_contribution"
    TAX = "tax"
    OTHER = "other"


class HrStatutoryCalcBasis(str, Enum):
    BASIC = "basic"
    GROSS = "gross"
    ELIGIBLE_COMPONENTS = "eligible_components"
    FIXED = "fixed"


class HrTaxFinancialYearStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"


class HrTaxDeclarationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    RETURNED = "returned"
    APPROVED = "approved"
    REJECTED = "rejected"


class HrTaxProofStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    RETURNED = "returned"


class HrSelfServiceRequestType(str, Enum):
    PROFILE_CORRECTION = "profile_correction"
    ADDRESS_UPDATE = "address_update"
    CONTACT_UPDATE = "contact_update"
    DOCUMENT_CORRECTION = "document_correction"
    ATTENDANCE_CORRECTION = "attendance_correction"
    LEAVE_CANCELLATION = "leave_cancellation"
    EMPLOYMENT_LETTER = "employment_letter"
    SERVICE_CERTIFICATE = "service_certificate"
    OTHER = "other"


class HrSelfServiceRequestStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class HrBenefitProgramStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class HrBenefitEnrollmentStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    CANCELLED = "cancelled"


class HrBenefitClaimStatus(str, Enum):
    AWAITING_REVIEW = "awaiting_review"
    UNDER_REVIEW = "under_review"
    RETURNED = "returned"
    APPROVED = "approved"
    PARTIALLY_APPROVED = "partially_approved"
    REJECTED = "rejected"
    AWAITING_PAYMENT = "awaiting_payment"
    PAID = "paid"
    PAYMENT_FAILED = "payment_failed"
    CANCELLED = "cancelled"


class HrBenefitClaimReviewAction(str, Enum):
    APPROVE = "approve"
    PARTIAL = "partial"
    REJECT = "reject"
    RETURN = "return"


class HrPerformanceCycleStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"


class HrPerformanceCycleKind(str, Enum):
    ANNUAL = "annual"
    HALF_YEARLY = "half_yearly"
    QUARTERLY = "quarterly"
    PROBATION = "probation"
    CUSTOM = "custom"


class HrPerformanceGoalStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class HrPerformanceReviewStatus(str, Enum):
    NOT_STARTED = "not_started"
    SELF_ASSESSMENT = "self_assessment"
    MANAGER_REVIEW = "manager_review"
    HR_REVIEW = "hr_review"
    RETURNED = "returned"
    FINALIZED = "finalized"


class HrPerformancePipStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class HrTrainingProgramStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class HrTrainingEnrollmentStatus(str, Enum):
    NOMINATED = "nominated"
    PENDING_APPROVAL = "pending_approval"
    WAITLISTED = "waitlisted"
    CONFIRMED = "confirmed"
    WITHDRAWN = "withdrawn"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class HrTrainingAttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    PARTIAL = "partial"


class HrDevelopmentPlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class HrAnnouncementStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class HrNotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class HrNotificationDeliveryStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    CANCELLED = "cancelled"


class HrReportExportFormat(str, Enum):
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"


class HrScheduledReportFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class HrPolicyLifecycleStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class HrAccessScopeKind(str, Enum):
    INSTITUTION = "institution"
    CAMPUS = "campus"
    DEPARTMENT = "department"
    EMPLOYEE_SET = "employee_set"


class HrTemporaryAccessStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"