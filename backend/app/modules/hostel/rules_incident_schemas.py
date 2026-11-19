"""Hostel rules and incidents API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.hostel.rules_incident_models import (
    HostelIncidentSeverity,
    HostelIncidentStatus,
    HostelRuleApprovalStatus,
    HostelRuleCategory,
    HostelRuleSeverity,
    HostelDisciplinaryOutcome,
)


class HostelRuleUpsertPortal(BaseModel):
    rule_code: str = Field(max_length=32)
    title: str = Field(max_length=300)
    body: str = Field(max_length=8000)
    category: HostelRuleCategory = HostelRuleCategory.OTHER
    hostel_codes: list[str] = Field(default_factory=list)
    resident_categories: list[str] = Field(default_factory=list)
    effective_from: date | None = None
    effective_to: date | None = None
    severity: HostelRuleSeverity = HostelRuleSeverity.MEDIUM
    requires_acknowledgement: bool = True
    consequence_policy: dict = Field(default_factory=dict)


class HostelRuleRead(BaseModel):
    rule_code: str
    title: str
    body: str
    category: HostelRuleCategory
    version: int
    published: bool
    approval_status: HostelRuleApprovalStatus
    effective_from: date | None
    updated_at: datetime


class RulePublishInput(BaseModel):
    rule_code: str
    approve: bool = True


class RuleAcknowledgeInput(BaseModel):
    rule_code: str


class IncidentReportInput(BaseModel):
    category: str
    description: str = Field(max_length=4000)
    hostel_code: str | None = None
    building_code: str | None = None
    block_code: str | None = None
    room_code: str | None = None
    incident_at: datetime | None = None
    severity: HostelIncidentSeverity = HostelIncidentSeverity.LOW
    immediate_action: str | None = None
    confidential: bool = False
    participant_user_ids: list[str] = Field(default_factory=list)


class IncidentRead(BaseModel):
    incident_id: str
    category: str
    description: str
    severity: HostelIncidentSeverity
    status: HostelIncidentStatus
    building_code: str | None
    confidential: bool
    allegation_only: bool
    created_at: datetime


class IncidentStatusUpdate(BaseModel):
    incident_id: str
    status: HostelIncidentStatus
    note: str | None = None


class IncidentInvestigationUpdate(BaseModel):
    incident_id: str
    notes: str | None = None
    finding_classification: str | None = None
    review_comments: str | None = None
    management_decision: str | None = None


class IncidentEvidenceInput(BaseModel):
    incident_id: str
    document_ref: str
    description: str | None = None
    restricted: bool = True


class DisciplinaryActionInput(BaseModel):
    incident_id: str
    student_user_id: str
    outcome: HostelDisciplinaryOutcome
    description: str = Field(max_length=2000)
    resident_response: str | None = None


class IncidentOverview(BaseModel):
    reported: int
    under_investigation: int
    awaiting_review: int
    resolved: int
    high_severity_open: int