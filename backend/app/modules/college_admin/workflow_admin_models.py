"""College admin workflow and approval collections."""

from datetime import datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class WorkflowModule(str, Enum):
    ADMISSIONS = "admissions"
    LEAVE = "leave"
    ATTENDANCE = "attendance"
    EXAMINATION = "examination"
    FINANCE = "finance"
    PROCUREMENT = "procurement"
    STUDENT_SERVICES = "student_services"
    HOSTEL = "hostel"
    LIBRARY = "library"
    CUSTOM = "custom"


class WorkflowInstanceStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    INFO_REQUESTED = "info_requested"


class ApprovalTaskStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    INFO_REQUESTED = "info_requested"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"


class StageApprovalMode(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


class InstitutionWorkflowDefinition(Document):
    tenant_id: PydanticObjectId
    workflow_key: str
    title: str
    module: WorkflowModule = WorkflowModule.CUSTOM
    version: int = 1
    is_active: bool = True
    allow_self_approval: bool = False
    required_permission: str | None = None
    condition_rules: list[dict[str, Any]] = Field(default_factory=list)
    cancellation_allowed: bool = True
    resubmission_allowed: bool = True
    updated_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_workflow_definitions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("workflow_key", ASCENDING), ("version", ASCENDING)],
                unique=True,
                name="unique_workflow_definition",
            ),
        ]


class InstitutionWorkflowStage(Document):
    tenant_id: PydanticObjectId
    workflow_key: str
    workflow_version: int
    stage_id: str
    stage_order: int = Field(ge=1)
    title: str
    approval_mode: StageApprovalMode = StageApprovalMode.SEQUENTIAL
    parallel_group: int = 1
    assignee_permission: str
    escalation_permission: str | None = None
    deadline_hours: int | None = Field(default=None, ge=1)
    skip_conditions: list[dict[str, Any]] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_workflow_stages"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("workflow_key", ASCENDING), ("workflow_version", ASCENDING), ("stage_id", ASCENDING)],
                unique=True,
                name="unique_workflow_stage",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("workflow_key", ASCENDING), ("stage_order", ASCENDING)],
                name="workflow_stages_order",
            ),
        ]


class InstitutionWorkflowInstance(Document):
    tenant_id: PydanticObjectId
    instance_id: str
    workflow_key: str
    workflow_version: int
    module: WorkflowModule
    resource_type: str
    resource_id: str
    requester_id: PydanticObjectId
    status: WorkflowInstanceStatus = WorkflowInstanceStatus.IN_PROGRESS
    current_stage_order: int = 1
    context: dict[str, Any] = Field(default_factory=dict)
    deadline_at: datetime | None = None
    cancelled_at: datetime | None = None
    completed_at: datetime | None = None
    parent_instance_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_workflow_instances"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("instance_id", ASCENDING)], unique=True, name="unique_workflow_instance"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING), ("updated_at", DESCENDING)], name="instances_by_status"),
            IndexModel([("tenant_id", ASCENDING), ("resource_type", ASCENDING), ("resource_id", ASCENDING)], name="instances_by_resource"),
        ]


class InstitutionApprovalTask(Document):
    tenant_id: PydanticObjectId
    task_id: str
    instance_id: str
    stage_id: str
    stage_order: int
    parallel_group: int = 1
    assignee_permission: str
    status: ApprovalTaskStatus = ApprovalTaskStatus.PENDING
    assigned_to_user_id: PydanticObjectId | None = None
    acted_by_user_id: PydanticObjectId | None = None
    comment: str | None = None
    deadline_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None

    class Settings:
        name = "institution_approval_tasks"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("task_id", ASCENDING)], unique=True, name="unique_approval_task"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING), ("deadline_at", ASCENDING)], name="pending_tasks"),
            IndexModel([("tenant_id", ASCENDING), ("instance_id", ASCENDING), ("stage_order", ASCENDING)], name="tasks_by_instance"),
        ]


class InstitutionApprovalHistory(Document):
    tenant_id: PydanticObjectId
    instance_id: str
    task_id: str | None = None
    event: str
    actor_id: PydanticObjectId | None = None
    summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_approval_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("instance_id", ASCENDING), ("created_at", DESCENDING)], name="approval_history"),
        ]


class InstitutionWorkflowDelegation(Document):
    tenant_id: PydanticObjectId
    delegation_id: str
    delegator_user_id: PydanticObjectId
    delegatee_user_id: PydanticObjectId
    workflow_keys: list[str] = Field(default_factory=list)
    valid_from: datetime = Field(default_factory=utcnow)
    valid_until: datetime
    active: bool = True
    created_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_workflow_delegations"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("delegation_id", ASCENDING)], unique=True, name="unique_delegation"),
            IndexModel([("tenant_id", ASCENDING), ("delegatee_user_id", ASCENDING), ("active", ASCENDING)], name="delegations_delegatee"),
        ]


class InstitutionWorkflowEscalation(Document):
    tenant_id: PydanticObjectId
    escalation_id: str
    instance_id: str
    task_id: str
    reason: str
    escalated_to_permission: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_workflow_escalations"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("instance_id", ASCENDING), ("created_at", DESCENDING)], name="escalations_instance"),
        ]