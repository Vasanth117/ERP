"""Examination cell — eligibility and registration enumerations."""

from enum import Enum


class ExamRegistrationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    CORRECTION_PENDING = "correction_pending"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class ExamRegistrationSubjectType(str, Enum):
    SEMESTER = "semester"
    ARREAR = "arrear"
    SUPPLEMENTARY = "supplementary"


class ExamRegistrationHistoryAction(str, Enum):
    CREATED = "created"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    CORRECTION_REQUESTED = "correction_requested"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    BULK_REGISTERED = "bulk_registered"


class ExamEligibilityRuleCode(str, Enum):
    STUDENT_ACTIVE = "student_active"
    ENROLLMENT = "enrollment"
    SESSION_OPEN = "session_open"
    ATTENDANCE = "attendance"
    FEE_CLEARANCE = "fee_clearance"
    ARREAR_POLICY = "arrear_policy"
    SUBJECT_ROSTER = "subject_roster"
    ASSESSMENT_CONFIG = "assessment_config"


class ExamHallTicketStatus(str, Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    PUBLISHED = "published"
    REVOKED = "revoked"
    REISSUED = "reissued"


class ExamHallTicketHistoryAction(str, Enum):
    GENERATED = "generated"
    PUBLISHED = "published"
    DOWNLOADED = "downloaded"
    REVOKED = "revoked"
    REISSUED = "reissued"
    CORRECTED = "corrected"