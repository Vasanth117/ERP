"""Hostel rules and incident collections."""

from datetime import date, datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class HostelRuleCategory(str, Enum):
    OPERATING_HOURS = "operating_hours"
    ENTRY_EXIT = "entry_exit"
    VISITING = "visiting"
    OUTPASS_LEAVE = "outpass_leave"
    MESS = "mess"
    CLEANLINESS = "cleanliness"
    CONDUCT = "conduct"
    SAFETY = "safety"
    EMERGENCY = "emergency"
    COMMON_FACILITY = "common_facility"
    OTHER = "other"


class HostelRuleApprovalStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class HostelRuleSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class HostelIncidentStatus(str, Enum):
    REPORTED = "reported"
    ACKNOWLEDGED = "acknowledged"
    UNDER_REVIEW = "under_review"
    UNDER_INVESTIGATION = "under_investigation"
    AWAITING_EVIDENCE = "awaiting_evidence"
    AWAITING_MGMT_REVIEW = "awaiting_mgmt_review"
    ACTION_REQUIRED = "action_required"
    RESOLVED = "resolved"
    CLOSED = "closed"
    DISMISSED = "dismissed"


class HostelIncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HostelDisciplinaryOutcome(str, Enum):
    WARNING = "warning"
    COUNSELLING = "counselling"
    WRITTEN_EXPLANATION = "written_explanation"
    FORMAL_REVIEW = "formal_review"
    RESTRICTED_PRIVILEGES = "restricted_privileges"
    OTHER = "other"


class HostelRule(Document):
    tenant_id: PydanticObjectId
    rule_code: str
    title: str
    body: str
    category: HostelRuleCategory = HostelRuleCategory.OTHER
    hostel_codes: list[str] = Field(default_factory=list)
    resident_categories: list[str] = Field(default_factory=list)
    effective_from: date | None = None
    effective_to: date | None = None
    severity: HostelRuleSeverity = HostelRuleSeverity.MEDIUM
    consequence_policy: dict[str, Any] = Field(default_factory=dict)
    approval_status: HostelRuleApprovalStatus = HostelRuleApprovalStatus.DRAFT
    requires_acknowledgement: bool = True
    version: int = 1
    published: bool = False
    published_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_rules"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("rule_code", ASCENDING)], unique=True, name="unique_hostel_rule"),
            IndexModel([("tenant_id", ASCENDING), ("published", ASCENDING), ("effective_from", DESCENDING)], name="rules_published"),
        ]


class HostelRuleVersion(Document):
    tenant_id: PydanticObjectId
    version_id: str
    rule_code: str
    version: int
    title: str
    body: str
    snapshot: dict[str, Any] = Field(default_factory=dict)
    published_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_rule_versions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("version_id", ASCENDING)], unique=True, name="unique_rule_version"),
            IndexModel([("tenant_id", ASCENDING), ("rule_code", ASCENDING), ("version", DESCENDING)], name="rule_versions"),
        ]


class HostelRuleAcknowledgement(Document):
    tenant_id: PydanticObjectId
    ack_id: str
    rule_code: str
    rule_version: int
    student_user_id: PydanticObjectId
    acknowledged_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_rule_acknowledgements"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("ack_id", ASCENDING)], unique=True, name="unique_rule_ack"),
            IndexModel(
                [("tenant_id", ASCENDING), ("rule_code", ASCENDING), ("student_user_id", ASCENDING), ("rule_version", ASCENDING)],
                unique=True,
                name="unique_ack_per_version",
            ),
        ]


class HostelIncident(Document):
    tenant_id: PydanticObjectId
    incident_id: str
    category: str
    hostel_code: str | None = None
    building_code: str | None = None
    block_code: str | None = None
    room_code: str | None = None
    incident_at: datetime = Field(default_factory=utcnow)
    description: str = Field(max_length=4000)
    severity: HostelIncidentSeverity = HostelIncidentSeverity.LOW
    status: HostelIncidentStatus = HostelIncidentStatus.REPORTED
    reporter_id: PydanticObjectId | None = None
    actor_id: PydanticObjectId | None = None
    immediate_action: str | None = None
    confidential: bool = False
    allegation_only: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_incidents"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("incident_id", ASCENDING)], unique=True, name="unique_hostel_incident"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING), ("severity", DESCENDING)], name="incidents_by_status"),
        ]


class HostelIncidentParticipant(Document):
    tenant_id: PydanticObjectId
    participant_id: str
    incident_id: str
    student_user_id: PydanticObjectId | None = None
    role: str
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_incident_participants"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("participant_id", ASCENDING)], unique=True, name="unique_incident_participant"),
            IndexModel([("tenant_id", ASCENDING), ("incident_id", ASCENDING)], name="participants_by_incident"),
        ]


class HostelIncidentEvidence(Document):
    tenant_id: PydanticObjectId
    evidence_id: str
    incident_id: str
    document_ref: str
    description: str | None = None
    restricted: bool = True
    uploaded_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_incident_evidence"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("evidence_id", ASCENDING)], unique=True, name="unique_incident_evidence"),
        ]


class HostelIncidentInvestigation(Document):
    tenant_id: PydanticObjectId
    investigation_id: str
    incident_id: str
    investigator_id: PydanticObjectId | None = None
    notes: str | None = Field(default=None, max_length=8000)
    finding_classification: str | None = None
    review_comments: str | None = None
    management_decision: str | None = None
    status: str = "open"
    started_at: datetime = Field(default_factory=utcnow)
    closed_at: datetime | None = None

    class Settings:
        name = "hostel_incident_investigations"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("investigation_id", ASCENDING)], unique=True, name="unique_incident_investigation"),
            IndexModel([("tenant_id", ASCENDING), ("incident_id", ASCENDING)], name="investigations_by_incident"),
        ]


class HostelIncidentAction(Document):
    tenant_id: PydanticObjectId
    action_id: str
    incident_id: str
    student_user_id: PydanticObjectId | None = None
    outcome: HostelDisciplinaryOutcome | None = None
    description: str
    approved_by: PydanticObjectId | None = None
    resident_response: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_incident_actions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("action_id", ASCENDING)], unique=True, name="unique_incident_action"),
        ]


class HostelIncidentHistory(Document):
    tenant_id: PydanticObjectId
    incident_id: str
    action: str
    detail: dict[str, Any] = Field(default_factory=dict)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_incident_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("incident_id", ASCENDING), ("created_at", DESCENDING)], name="incident_history"),
        ]