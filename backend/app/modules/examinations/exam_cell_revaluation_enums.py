"""Revaluation and supplementary enumerations."""

from enum import Enum


class ExamRevaluationApplicationType(str, Enum):
    REVALUATION = "revaluation"
    RECHECKING = "rechecking"


class ExamRevaluationApplicationStatus(str, Enum):
    SUBMITTED = "submitted"
    FEE_PENDING = "fee_pending"
    FEE_VERIFIED = "fee_verified"
    ASSIGNED = "assigned"
    UNDER_EVALUATION = "under_evaluation"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ExamRevaluationHistoryAction(str, Enum):
    CREATED = "created"
    FEE_VERIFIED = "fee_verified"
    EVALUATOR_ASSIGNED = "evaluator_assigned"
    EVALUATION_RECORDED = "evaluation_recorded"
    APPROVED = "approved"
    REJECTED = "rejected"
    MARKS_APPLIED = "marks_applied"
    GRADES_RECALCULATED = "grades_recalculated"
    REVISED_PUBLISHED = "revised_published"


class ExamSupplementaryRegistrationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    FEE_VERIFIED = "fee_verified"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class ExamIncidentType(str, Enum):
    DISRUPTION = "disruption"
    MALPRACTICE_ALLEGATION = "malpractice_allegation"
    SAFETY = "safety"
    TECHNICAL = "technical"
    OTHER = "other"


class ExamIncidentStatus(str, Enum):
    REPORTED = "reported"
    UNDER_INVESTIGATION = "under_investigation"
    COMMITTEE_REVIEW = "committee_review"
    DECISION_RECORDED = "decision_recorded"
    CLOSED = "closed"
    APPEAL_PENDING = "appeal_pending"


class ExamMalpracticeCaseStatus(str, Enum):
    ALLEGED = "alleged"
    INVESTIGATING = "investigating"
    COMMITTEE_REVIEW = "committee_review"
    PROVEN = "proven"
    NOT_PROVEN = "not_proven"
    WITHHELD = "withheld"
    CLOSED = "closed"


class ExamDisciplinaryActionType(str, Enum):
    WARNING = "warning"
    RESULT_WITHHELD = "result_withheld"
    SUSPENSION = "suspension"
    OTHER = "other"


class ExamIncidentHistoryAction(str, Enum):
    REPORTED = "reported"
    EVIDENCE_ADDED = "evidence_added"
    INVESTIGATOR_ASSIGNED = "investigator_assigned"
    STATEMENT_RECORDED = "statement_recorded"
    FINDING_RECORDED = "finding_recorded"
    DECISION_RECORDED = "decision_recorded"
    APPEAL_FILED = "appeal_filed"
    CLOSED = "closed"
    WITHHOLDING_APPLIED = "withholding_applied"