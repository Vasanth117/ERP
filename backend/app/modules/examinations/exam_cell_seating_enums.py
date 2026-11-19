"""Examination cell — seating and logistics enumerations."""

from enum import Enum


class ExamSeatingPolicy(str, Enum):
    DEPARTMENT = "department"
    PROGRAMME = "programme"
    MIXED = "mixed"


class ExamSeatingPlanStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ExamSeatingAllocationStatus(str, Enum):
    ALLOCATED = "allocated"
    CHANGED = "changed"
    REVOKED = "revoked"


class ExamInvigilatorRole(str, Enum):
    CHIEF = "chief"
    INVIGILATOR = "invigilator"


class ExamDutyHistoryKind(str, Enum):
    SEATING = "seating"
    INVIGILATION = "invigilation"


class ExamDutyHistoryAction(str, Enum):
    CREATED = "created"
    ALLOCATED = "allocated"
    CHANGED = "changed"
    REVOKED = "revoked"
    PUBLISHED = "published"
    APPROVED = "approved"