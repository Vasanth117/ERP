"""Workflow administration API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.college_admin.workflow_admin_models import (
    ApprovalTaskStatus,
    StageApprovalMode,
    WorkflowInstanceStatus,
    WorkflowModule,
)


class WorkflowStageUpsert(BaseModel):
    stage_id: str
    stage_order: int = Field(ge=1)
    title: str
    approval_mode: StageApprovalMode = StageApprovalMode.SEQUENTIAL
    parallel_group: int = 1
    assignee_permission: str
    escalation_permission: str | None = None
    deadline_hours: int | None = Field(default=None, ge=1)
    skip_conditions: list[dict[str, Any]] = Field(default_factory=list)


class WorkflowDefinitionUpsert(BaseModel):
    workflow_key: str
    title: str
    module: WorkflowModule = WorkflowModule.CUSTOM
    allow_self_approval: bool = False
    required_permission: str | None = None
    condition_rules: list[dict[str, Any]] = Field(default_factory=list)
    cancellation_allowed: bool = True
    resubmission_allowed: bool = True
    stages: list[WorkflowStageUpsert] = Field(default_factory=list)


class WorkflowDefinitionRead(BaseModel):
    workflow_key: str
    title: str
    module: WorkflowModule
    version: int
    is_active: bool
    allow_self_approval: bool
    required_permission: str | None
    stage_count: int


class WorkflowInstanceStart(BaseModel):
    workflow_key: str
    resource_type: str
    resource_id: str
    context: dict[str, Any] = Field(default_factory=dict)


class WorkflowInstanceRead(BaseModel):
    instance_id: str
    workflow_key: str
    module: WorkflowModule
    resource_type: str
    resource_id: str
    requester_id: str
    status: WorkflowInstanceStatus
    current_stage_order: int
    created_at: datetime
    deadline_at: datetime | None


class ApprovalTaskRead(BaseModel):
    task_id: str
    instance_id: str
    stage_id: str
    stage_order: int
    assignee_permission: str
    status: ApprovalTaskStatus
    deadline_at: datetime | None
    comment: str | None


class ApprovalDecision(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)


class ApprovalReject(ApprovalDecision):
    reason: str = Field(min_length=1, max_length=500)


class ApprovalInfoRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class WorkflowDelegationCreate(BaseModel):
    delegation_id: str
    delegatee_user_id: str
    workflow_keys: list[str] = Field(default_factory=list)
    valid_until: datetime


class WorkflowDelegationRead(BaseModel):
    delegation_id: str
    delegator_user_id: str
    delegatee_user_id: str
    workflow_keys: list[str]
    valid_until: datetime
    active: bool


class ApprovalHistoryItem(BaseModel):
    instance_id: str
    task_id: str | None
    event: str
    actor_id: str | None
    summary: str
    created_at: datetime


class WorkflowEscalationRead(BaseModel):
    escalation_id: str
    instance_id: str
    task_id: str
    reason: str
    created_at: datetime