"""Parent / guardian portal enumerations."""

from enum import Enum


class ParentAccountStatus(str, Enum):
    PENDING_ACTIVATION = "pending_activation"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATION_REQUESTED = "deactivation_requested"
    DEACTIVATED = "deactivated"


class ParentContactVerificationChannel(str, Enum):
    EMAIL = "email"
    MOBILE = "mobile"


class ParentContactVerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    FAILED = "failed"


class ParentProfileChangeStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ParentRelationshipType(str, Enum):
    FATHER = "father"
    MOTHER = "mother"
    LEGAL_GUARDIAN = "legal_guardian"
    APPROVED_GUARDIAN = "approved_guardian"
    OTHER = "other"


class ParentLinkRequestStatus(str, Enum):
    REQUESTED = "requested"
    PENDING_VERIFICATION = "pending_verification"
    ADDITIONAL_INFO_REQUIRED = "additional_information_required"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class ParentRelationshipStatus(str, Enum):
    REQUESTED = "requested"
    PENDING_VERIFICATION = "pending_verification"
    ADDITIONAL_INFO_REQUIRED = "additional_information_required"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOCATION_REQUESTED = "revocation_requested"
    REVOKED = "revoked"
    EXPIRED = "expired"


class ParentVerificationMethod(str, Enum):
    MANUAL_INSTITUTIONAL = "manual_institutional"
    DOCUMENT_REVIEW = "document_review"
    STUDENT_CONFIRMATION = "student_confirmation"
    VERIFIED_CONTACT_MATCH = "verified_contact_match"
    OTHER = "other"


class ParentDataPermission(str, Enum):
    """Granular data access granted per verified parent–student relationship."""

    VIEW_PROFILE = "view_profile"
    VIEW_ATTENDANCE = "view_attendance"
    VIEW_RESULTS = "view_results"
    VIEW_EXAM_TIMETABLE = "view_exam_timetable"
    VIEW_FEES = "view_fees"
    PAY_FEES = "pay_fees"
    VIEW_RECEIPTS = "view_receipts"
    RECEIVE_ANNOUNCEMENTS = "receive_announcements"
    SUBMIT_SERVICE_REQUESTS = "submit_service_requests"
    REQUEST_MEETINGS = "request_meetings"
    VIEW_HOSTEL = "view_hostel"
    VIEW_LIBRARY = "view_library"
    VIEW_TRANSPORT = "view_transport"
    VIEW_HALL_TICKET = "view_hall_ticket"


# Default grants when a relationship is approved (institution may override on approval).
DEFAULT_RELATIONSHIP_PERMISSIONS: dict[str, bool] = {
    ParentDataPermission.VIEW_PROFILE.value: True,
    ParentDataPermission.VIEW_ATTENDANCE.value: True,
    ParentDataPermission.VIEW_RESULTS.value: True,
    ParentDataPermission.VIEW_EXAM_TIMETABLE.value: True,
    ParentDataPermission.VIEW_FEES.value: True,
    ParentDataPermission.PAY_FEES.value: False,
    ParentDataPermission.VIEW_RECEIPTS.value: True,
    ParentDataPermission.RECEIVE_ANNOUNCEMENTS.value: True,
    ParentDataPermission.SUBMIT_SERVICE_REQUESTS.value: True,
    ParentDataPermission.REQUEST_MEETINGS.value: True,
    ParentDataPermission.VIEW_HOSTEL.value: True,
    ParentDataPermission.VIEW_LIBRARY.value: False,
    ParentDataPermission.VIEW_TRANSPORT.value: True,
    ParentDataPermission.VIEW_HALL_TICKET.value: False,
}


class ParentFinanceEnquiryCategory(str, Enum):
    PAYMENT_DISCREPANCY = "payment_discrepancy"
    FAILED_PAYMENT = "failed_payment"
    DUPLICATE_PAYMENT = "duplicate_payment"
    RECEIPT_CORRECTION = "receipt_correction"
    REFUND_STATUS = "refund_status"
    OTHER = "other"


class ParentFinanceEnquiryStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    RESPONDED = "responded"
    CLOSED = "closed"


class ParentDashboardDateRange(str, Enum):
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"


class ParentNotificationCategory(str, Enum):
    ACADEMIC = "academic"
    FINANCE = "finance"
    ANNOUNCEMENT = "announcement"
    REQUEST = "request"
    SECURITY = "security"
    OTHER = "other"


ACTIVE_RELATIONSHIP_STATUSES = frozenset(
    {
        ParentRelationshipStatus.ACTIVE,
        ParentRelationshipStatus.VERIFIED,
    }
)

PENDING_LINK_STATUSES = frozenset(
    {
        ParentLinkRequestStatus.REQUESTED,
        ParentLinkRequestStatus.PENDING_VERIFICATION,
        ParentLinkRequestStatus.ADDITIONAL_INFO_REQUIRED,
        ParentLinkRequestStatus.UNDER_REVIEW,
    }
)


class ParentAcademicEnquiryCategory(str, Enum):
    PROFILE_DISCREPANCY = "profile_discrepancy"
    ACADEMIC_RECORD = "academic_record"
    ENROLLMENT = "enrollment"
    OTHER = "other"


class ParentAcademicEnquiryStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    RESPONDED = "responded"
    CLOSED = "closed"


class ParentAttendanceEnquiryCategory(str, Enum):
    MISSING_MARK = "missing_mark"
    INCORRECT_STATUS = "incorrect_status"
    UNEXPECTED_ABSENCE = "unexpected_absence"
    SUBJECT_DISCREPANCY = "subject_discrepancy"
    SHORTAGE_CLARIFICATION = "shortage_clarification"
    OTHER = "other"


class ParentAttendanceEnquiryStatus(str, Enum):
    SUBMITTED = "submitted"
    ASSIGNED = "assigned"
    UNDER_REVIEW = "under_review"
    RESPONDED = "responded"
    CLOSED = "closed"


class ParentAttendanceAlertSeverity(str, Enum):
    WARNING = "warning"
    CRITICAL = "critical"


class ParentCommunicationInboxCategory(str, Enum):
    INSTITUTIONAL = "institutional"
    ACADEMIC = "academic"
    ATTENDANCE = "attendance"
    EXAMINATION = "examination"
    FINANCE = "finance"
    SCHOLARSHIP = "scholarship"
    SERVICE_REQUEST = "service_request"
    PARENT_ACTIVITY = "parent_activity"
    MEETING = "meeting"
    HOSTEL = "hostel"
    TRANSPORT = "transport"
    LIBRARY = "library"
    SECURITY = "security"
    OTHER = "other"


class ParentNotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ParentServiceRequestCategory(str, Enum):
    ACADEMIC = "academic"
    ADMINISTRATIVE = "administrative"
    FINANCIAL = "financial"
    STUDENT_SERVICE = "student_service"
    OTHER = "other"


class ParentServiceRequestStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    RECEIVED = "received"
    ASSIGNED = "assigned"
    UNDER_REVIEW = "under_review"
    AWAITING_INFORMATION = "awaiting_information"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class ParentDocumentAccessRequestStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class ParentSupportEnquiryCategory(str, Enum):
    ACCOUNT = "parent_account"
    LINKING = "student_linking"
    DOCUMENT_ACCESS = "document_access"
    TECHNICAL = "technical"
    GENERAL = "general"


class ParentSupportEnquiryStatus(str, Enum):
    SUBMITTED = "submitted"
    ROUTED = "routed"
    UNDER_REVIEW = "under_review"
    RESPONDED = "responded"
    CLOSED = "closed"


# Institution-configurable request types (category -> allowed type codes).
PARENT_SERVICE_REQUEST_TYPES: dict[str, list[str]] = {
    ParentServiceRequestCategory.ACADEMIC.value: [
        "academic_information",
        "course_enquiry",
        "progress_enquiry",
        "attendance_discrepancy",
        "examination_information",
        "result_clarification",
        "transcript_enquiry",
    ],
    ParentServiceRequestCategory.ADMINISTRATIVE.value: [
        "bonafide_certificate",
        "study_certificate",
        "student_information",
        "detail_correction",
        "general_administrative",
    ],
    ParentServiceRequestCategory.FINANCIAL.value: [
        "fee_clarification",
        "payment_discrepancy",
        "failed_payment",
        "receipt_issue",
        "scholarship_clarification",
        "refund_status",
    ],
    ParentServiceRequestCategory.STUDENT_SERVICE.value: [
        "hostel_enquiry",
        "transport_enquiry",
        "library_enquiry",
        "student_welfare",
        "other_service",
    ],
    ParentServiceRequestCategory.OTHER.value: ["general"],
}

class ParentMeetingMode(str, Enum):
    IN_PERSON = "in_person"
    ONLINE = "online"
    PHONE = "phone"


class ParentMeetingRequestStatus(str, Enum):
    SUBMITTED = "submitted"
    PENDING_STAFF = "pending_staff"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    RESCHEDULE_REQUESTED = "reschedule_requested"
    COMPLETED = "completed"
    MISSED = "missed"


class ParentMeetingAppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    MISSED = "missed"


DEFAULT_PARENT_MEETING_CATEGORIES: list[tuple[str, str]] = [
    ("class_advisor", "Parent–Class Advisor Meeting"),
    ("faculty", "Parent–Faculty Meeting"),
    ("hod", "Parent–HOD Meeting"),
    ("principal", "Parent–Principal Meeting"),
    ("academic_progress", "Academic Progress Meeting"),
    ("attendance", "Attendance Shortage Discussion"),
    ("examination", "Examination Performance Discussion"),
    ("welfare", "Student Welfare Meeting"),
    ("financial", "Financial Enquiry Meeting"),
    ("hostel", "Hostel-related Meeting"),
    ("transport", "Transport-related Meeting"),
    ("other", "Other"),
]


class ParentReportCategory(str, Enum):
    ACADEMIC = "academic"
    ATTENDANCE = "attendance"
    EXAMINATION = "examination"
    FINANCE = "finance"
    STUDENT_SERVICES = "student_services"
    PARENT_ACTIVITY = "parent_activity"
    CONSOLIDATED = "consolidated"


class ParentStudentServiceType(str, Enum):
    HOSTEL = "hostel"
    MESS = "mess"
    LIBRARY = "library"
    TRANSPORT = "transport"
    WELFARE = "welfare"
    OTHER = "other"


class ParentRelationshipReviewAction(str, Enum):
    PERMISSION_REVIEW = "permission_review"
    RELATIONSHIP_REMOVAL = "relationship_removal"


MANDATORY_PARENT_NOTIFICATION_CATEGORIES = frozenset(
    {
        ParentCommunicationInboxCategory.SECURITY.value,
        ParentCommunicationInboxCategory.PARENT_ACTIVITY.value,
    }
)