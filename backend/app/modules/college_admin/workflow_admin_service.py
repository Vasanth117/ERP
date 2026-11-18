"""Institutional workflow and approval engine."""

from datetime import timedelta
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.college_admin.workflow_admin_models import (
    ApprovalTaskStatus,
    InstitutionApprovalHistory,
    InstitutionApprovalTask,
    InstitutionWorkflowDefinition,
    InstitutionWorkflowEscalation,
    InstitutionWorkflowDelegation,
    InstitutionWorkflowInstance,
    InstitutionWorkflowStage,
    StageApprovalMode,
    WorkflowInstanceStatus,
    WorkflowModule,
)
from app.modules.college_admin.workflow_admin_schemas import (
    ApprovalDecision,
    ApprovalHistoryItem,
    ApprovalInfoRequest,
    ApprovalReject,
    ApprovalTaskRead,
    WorkflowDefinitionRead,
    WorkflowDefinitionUpsert,
    WorkflowDelegationCreate,
    WorkflowDelegationRead,
    WorkflowEscalationRead,
    WorkflowInstanceRead,
    WorkflowInstanceStart,
)

_BUILTIN: list[dict] = [
    {
        "workflow_key": "leave",
        "title": "Employee leave approval",
        "module": WorkflowModule.LEAVE,
        "required_permission": Permission.HR_ADMIN_LEAVE_APPROVE.value,
        "stages": [
            {
                "stage_id": "manager",
                "stage_order": 1,
                "title": "Reporting manager",
                "assignee_permission": Permission.HR_ADMIN_MANAGE.value,
            },
            {
                "stage_id": "hr",
                "stage_order": 2,
                "title": "HR approval",
                "assignee_permission": Permission.HR_ADMIN_LEAVE_APPROVE.value,
            },
        ],
    },
    {
        "workflow_key": "attendance_correction",
        "title": "Attendance correction",
        "module": WorkflowModule.ATTENDANCE,
        "required_permission": Permission.ATTENDANCE_ADMIN_MANAGE.value,
        "stages": [
            {
                "stage_id": "review",
                "stage_order": 1,
                "title": "Attendance admin review",
                "assignee_permission": Permission.ATTENDANCE_ADMIN_MANAGE.value,
            },
        ],
    },
    {
        "workflow_key": "finance_approval",
        "title": "Financial approval",
        "module": WorkflowModule.FINANCE,
        "required_permission": Permission.FINANCE_ADMIN_APPROVE.value,
        "stages": [
            {
                "stage_id": "finance_officer",
                "stage_order": 1,
                "title": "Finance officer",
                "assignee_permission": Permission.FINANCE_ADMIN_MANAGE.value,
            },
            {
                "stage_id": "finance_head",
                "stage_order": 2,
                "title": "Finance head",
                "assignee_permission": Permission.FINANCE_ADMIN_APPROVE.value,
            },
        ],
    },
]


async def _seed_builtin_definition(tenant_id: PydanticObjectId, item: dict) -> None:
    key = item["workflow_key"]
    existing = await InstitutionWorkflowDefinition.find_one(
        Eq(InstitutionWorkflowDefinition.tenant_id, tenant_id),
        Eq(InstitutionWorkflowDefinition.workflow_key, key),
        Eq(InstitutionWorkflowDefinition.is_active, True),
    )
    if existing is not None:
        return
    definition = InstitutionWorkflowDefinition(
        tenant_id=tenant_id,
        workflow_key=key,
        title=item["title"],
        module=item["module"],
        version=1,
        required_permission=item.get("required_permission"),
    )
    await definition.insert()
    for st in item["stages"]:
        await InstitutionWorkflowStage(
            tenant_id=tenant_id,
            workflow_key=key,
            workflow_version=1,
            stage_id=st["stage_id"],
            stage_order=st["stage_order"],
            title=st["title"],
            assignee_permission=st["assignee_permission"],
        ).insert()


async def _ensure_builtin_workflows(tenant_id: PydanticObjectId) -> None:
    for item in _BUILTIN:
        await _seed_builtin_definition(tenant_id, item)


def _has_permission(scope: AccessScope, code: str) -> bool:
    try:
        authorize(scope, Permission(code))
        return True
    except AppError:
        return False


def _stage_skipped(stage: InstitutionWorkflowStage, context: dict) -> bool:
    for rule in stage.skip_conditions:
        field = rule.get("field")
        op = rule.get("op", "eq")
        expected = rule.get("value")
        actual = context.get(field)
        if op == "eq" and actual == expected:
            return True
        if op == "lt" and actual is not None and actual < expected:
            return True
        if op == "gt" and actual is not None and actual > expected:
            return True
    return False


async def _history(
    tenant_id: PydanticObjectId,
    instance_id: str,
    event: str,
    summary: str,
    *,
    actor_id: PydanticObjectId | None,
    task_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    await InstitutionApprovalHistory(
        tenant_id=tenant_id,
        instance_id=instance_id,
        task_id=task_id,
        event=event,
        actor_id=actor_id,
        summary=summary,
        metadata=metadata or {},
    ).insert()


async def _active_delegation(
    tenant_id: PydanticObjectId,
    delegatee_id: PydanticObjectId,
    workflow_key: str,
) -> InstitutionWorkflowDelegation | None:
    now = utcnow()
    rows = await InstitutionWorkflowDelegation.find(
        Eq(InstitutionWorkflowDelegation.tenant_id, tenant_id),
        Eq(InstitutionWorkflowDelegation.delegatee_user_id, delegatee_id),
        Eq(InstitutionWorkflowDelegation.active, True),
    ).to_list()
    for row in rows:
        until = row.valid_until
        if until.tzinfo is None:
            until = until.replace(tzinfo=now.tzinfo)
        if until < now:
            continue
        if not row.workflow_keys or workflow_key in row.workflow_keys:
            return row
    return None


async def upsert_workflow_definition(
    scope: AccessScope,
    user: User,
    payload: WorkflowDefinitionUpsert,
    *,
    _skip_auth: bool = False,
) -> WorkflowDefinitionRead:
    if not _skip_auth:
        authorize(scope, Permission.WORKFLOW_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope) if not _skip_auth else user.tenant_id
    key = payload.workflow_key.strip().lower()
    if not payload.stages:
        raise AppError(code="VALIDATION_ERROR", message="At least one stage required", status_code=422)
    latest = await InstitutionWorkflowDefinition.find(
        Eq(InstitutionWorkflowDefinition.tenant_id, tenant_id),
        Eq(InstitutionWorkflowDefinition.workflow_key, key),
    ).sort("-version").first_or_none()
    version = 1 if latest is None else latest.version + 1
    if latest:
        latest.is_active = False
        await latest.save()
    definition = InstitutionWorkflowDefinition(
        tenant_id=tenant_id,
        workflow_key=key,
        title=payload.title,
        module=payload.module,
        version=version,
        allow_self_approval=payload.allow_self_approval,
        required_permission=payload.required_permission,
        condition_rules=payload.condition_rules,
        cancellation_allowed=payload.cancellation_allowed,
        resubmission_allowed=payload.resubmission_allowed,
        updated_by=None if _skip_auth else user.id,
    )
    await definition.insert()
    for st in payload.stages:
        await InstitutionWorkflowStage(
            tenant_id=tenant_id,
            workflow_key=key,
            workflow_version=version,
            stage_id=st.stage_id.strip().lower(),
            stage_order=st.stage_order,
            title=st.title,
            approval_mode=st.approval_mode,
            parallel_group=st.parallel_group,
            assignee_permission=st.assignee_permission,
            escalation_permission=st.escalation_permission,
            deadline_hours=st.deadline_hours,
            skip_conditions=st.skip_conditions,
        ).insert()
    if not _skip_auth:
        await append_institution_audit(
            tenant_id,
            actor_id=user.id,
            action="workflow.definition.upsert",
            module="workflow",
            resource_type="workflow_definition",
            resource_id=key,
            metadata={"version": version},
        )
    return WorkflowDefinitionRead(
        workflow_key=key,
        title=payload.title,
        module=payload.module,
        version=version,
        is_active=True,
        allow_self_approval=payload.allow_self_approval,
        required_permission=payload.required_permission,
        stage_count=len(payload.stages),
    )


async def list_workflow_definitions(scope: AccessScope) -> list[WorkflowDefinitionRead]:
    authorize(scope, Permission.WORKFLOW_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    await _ensure_builtin_workflows(tenant_id)
    docs = await InstitutionWorkflowDefinition.find(
        Eq(InstitutionWorkflowDefinition.tenant_id, tenant_id),
        Eq(InstitutionWorkflowDefinition.is_active, True),
    ).to_list()
    result: list[WorkflowDefinitionRead] = []
    for d in docs:
        count = await InstitutionWorkflowStage.find(
            Eq(InstitutionWorkflowStage.tenant_id, tenant_id),
            Eq(InstitutionWorkflowStage.workflow_key, d.workflow_key),
            Eq(InstitutionWorkflowStage.workflow_version, d.version),
        ).count()
        result.append(
            WorkflowDefinitionRead(
                workflow_key=d.workflow_key,
                title=d.title,
                module=d.module,
                version=d.version,
                is_active=d.is_active,
                allow_self_approval=d.allow_self_approval,
                required_permission=d.required_permission,
                stage_count=count,
            )
        )
    return result


async def _spawn_stage_tasks(
    instance: InstitutionWorkflowInstance,
    stage_order: int,
) -> bool:
    stages = await InstitutionWorkflowStage.find(
        Eq(InstitutionWorkflowStage.tenant_id, instance.tenant_id),
        Eq(InstitutionWorkflowStage.workflow_key, instance.workflow_key),
        Eq(InstitutionWorkflowStage.workflow_version, instance.workflow_version),
        Eq(InstitutionWorkflowStage.stage_order, stage_order),
    ).to_list()
    if not stages:
        return False
    spawned = False
    for stage in stages:
        if _stage_skipped(stage, instance.context):
            continue
        deadline = None
        if stage.deadline_hours:
            deadline = utcnow() + timedelta(hours=stage.deadline_hours)
        task_id = f"tsk_{uuid4().hex[:12]}"
        await InstitutionApprovalTask(
            tenant_id=instance.tenant_id,
            task_id=task_id,
            instance_id=instance.instance_id,
            stage_id=stage.stage_id,
            stage_order=stage.stage_order,
            parallel_group=stage.parallel_group,
            assignee_permission=stage.assignee_permission,
            deadline_at=deadline,
        ).insert()
        spawned = True
    if spawned:
        instance.current_stage_order = stage_order
        instance.updated_at = utcnow()
        await instance.save()
    return spawned


async def start_workflow_instance(scope: AccessScope, user: User, payload: WorkflowInstanceStart) -> WorkflowInstanceRead:
    authorize(scope, Permission.WORKFLOW_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    await _ensure_builtin_workflows(tenant_id)
    key = payload.workflow_key.strip().lower()
    definition = await InstitutionWorkflowDefinition.find_one(
        Eq(InstitutionWorkflowDefinition.tenant_id, tenant_id),
        Eq(InstitutionWorkflowDefinition.workflow_key, key),
        Eq(InstitutionWorkflowDefinition.is_active, True),
    )
    if definition is None:
        raise AppError(code="NOT_FOUND", message="Workflow definition not found", status_code=404)
    if definition.required_permission and not _has_permission(scope, definition.required_permission):
        raise AppError(code="FORBIDDEN", message="Cannot start this workflow", status_code=403)
    existing = await InstitutionWorkflowInstance.find_one(
        Eq(InstitutionWorkflowInstance.tenant_id, tenant_id),
        Eq(InstitutionWorkflowInstance.resource_type, payload.resource_type),
        Eq(InstitutionWorkflowInstance.resource_id, payload.resource_id),
        In(InstitutionWorkflowInstance.status, [WorkflowInstanceStatus.IN_PROGRESS, WorkflowInstanceStatus.INFO_REQUESTED]),
    )
    if existing:
        raise AppError(code="CONFLICT", message="Active workflow already exists for resource", status_code=409)
    instance_id = f"wfi_{uuid4().hex[:12]}"
    instance = InstitutionWorkflowInstance(
        tenant_id=tenant_id,
        instance_id=instance_id,
        workflow_key=key,
        workflow_version=definition.version,
        module=definition.module,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        requester_id=user.id,
        status=WorkflowInstanceStatus.IN_PROGRESS,
        context=payload.context,
    )
    await instance.insert()
    await _history(tenant_id, instance_id, "started", f"Workflow {key} started", actor_id=user.id)
    await _spawn_stage_tasks(instance, 1)
    await append_institution_audit(
        tenant_id,
        actor_id=user.id,
        action="workflow.instance.start",
        module="workflow",
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        metadata={"instance_id": instance_id, "workflow_key": key},
    )
    return _instance_read(instance)


def _instance_read(doc: InstitutionWorkflowInstance) -> WorkflowInstanceRead:
    return WorkflowInstanceRead(
        instance_id=doc.instance_id,
        workflow_key=doc.workflow_key,
        module=doc.module,
        resource_type=doc.resource_type,
        resource_id=doc.resource_id,
        requester_id=str(doc.requester_id),
        status=doc.status,
        current_stage_order=doc.current_stage_order,
        created_at=doc.created_at,
        deadline_at=doc.deadline_at,
    )


def _task_read(doc: InstitutionApprovalTask) -> ApprovalTaskRead:
    return ApprovalTaskRead(
        task_id=doc.task_id,
        instance_id=doc.instance_id,
        stage_id=doc.stage_id,
        stage_order=doc.stage_order,
        assignee_permission=doc.assignee_permission,
        status=doc.status,
        deadline_at=doc.deadline_at,
        comment=doc.comment,
    )


async def _can_act_on_task(
    scope: AccessScope,
    user: User,
    task: InstitutionApprovalTask,
    instance: InstitutionWorkflowInstance,
    definition: InstitutionWorkflowDefinition,
) -> None:
    if task.status != ApprovalTaskStatus.PENDING:
        raise AppError(code="VALIDATION_ERROR", message="Task is not pending", status_code=422)
    allowed = _has_permission(scope, task.assignee_permission)
    delegation = await _active_delegation(instance.tenant_id, user.id, instance.workflow_key)
    if delegation and not allowed:
        delegator = await User.get(delegation.delegator_user_id)
        if delegator and delegator.tenant_id == instance.tenant_id:
            pseudo_scope = AccessScope(
                role=scope.role,
                user_id=delegation.delegator_user_id,
                tenant_id=scope.tenant_id,
                department_id=scope.department_id,
                effective_permissions=scope.effective_permissions,
            )
            allowed = _has_permission(pseudo_scope, task.assignee_permission)
    if not allowed:
        raise AppError(code="FORBIDDEN", message="Not authorized for this approval task", status_code=403)
    if not definition.allow_self_approval and instance.requester_id == user.id:
        from app.modules.college_admin.security_admin_service import get_security_policy

        policy = await get_security_policy(scope)
        if policy.block_self_approval:
            raise AppError(code="FORBIDDEN", message="Self-approval is not permitted", status_code=403)


async def list_pending_approval_tasks(scope: AccessScope, pagination: Pagination) -> Page[ApprovalTaskRead]:
    authorize(scope, Permission.WORKFLOW_ADMIN_APPROVE)
    tenant_id = require_college_tenant_scope(scope)
    docs = await InstitutionApprovalTask.find(
        Eq(InstitutionApprovalTask.tenant_id, tenant_id),
        Eq(InstitutionApprovalTask.status, ApprovalTaskStatus.PENDING),
    ).sort("-created_at").to_list()
    visible: list[InstitutionApprovalTask] = []
    for task in docs:
        if _has_permission(scope, task.assignee_permission):
            visible.append(task)
            continue
        instance = await InstitutionWorkflowInstance.find_one(
            Eq(InstitutionWorkflowInstance.tenant_id, tenant_id),
            Eq(InstitutionWorkflowInstance.instance_id, task.instance_id),
        )
        if instance and await _active_delegation(tenant_id, scope.user_id, instance.workflow_key):
            visible.append(task)
    slice_ = visible[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=[_task_read(t) for t in slice_], total=len(visible), limit=pagination.limit, offset=pagination.offset)


async def approve_task(scope: AccessScope, user: User, task_id: str, payload: ApprovalDecision) -> ApprovalTaskRead:
    authorize(scope, Permission.WORKFLOW_ADMIN_APPROVE)
    tenant_id = require_college_tenant_scope(scope)
    task = await InstitutionApprovalTask.find_one(
        Eq(InstitutionApprovalTask.tenant_id, tenant_id),
        Eq(InstitutionApprovalTask.task_id, task_id),
    )
    if task is None:
        raise AppError(code="NOT_FOUND", message="Approval task not found", status_code=404)
    instance = await InstitutionWorkflowInstance.find_one(
        Eq(InstitutionWorkflowInstance.tenant_id, tenant_id),
        Eq(InstitutionWorkflowInstance.instance_id, task.instance_id),
    )
    if instance is None:
        raise AppError(code="NOT_FOUND", message="Workflow instance not found", status_code=404)
    definition = await InstitutionWorkflowDefinition.find_one(
        Eq(InstitutionWorkflowDefinition.tenant_id, tenant_id),
        Eq(InstitutionWorkflowDefinition.workflow_key, instance.workflow_key),
        Eq(InstitutionWorkflowDefinition.version, instance.workflow_version),
    )
    if definition is None:
        raise AppError(code="NOT_FOUND", message="Workflow definition not found", status_code=404)
    await _can_act_on_task(scope, user, task, instance, definition)
    task.status = ApprovalTaskStatus.APPROVED
    task.acted_by_user_id = user.id
    task.comment = payload.comment
    task.completed_at = utcnow()
    await task.save()
    await _history(tenant_id, instance.instance_id, "approved", "Task approved", actor_id=user.id, task_id=task_id)
    peers = await InstitutionApprovalTask.find(
        Eq(InstitutionApprovalTask.tenant_id, tenant_id),
        Eq(InstitutionApprovalTask.instance_id, instance.instance_id),
        Eq(InstitutionApprovalTask.stage_order, task.stage_order),
    ).to_list()
    stage = await InstitutionWorkflowStage.find_one(
        Eq(InstitutionWorkflowStage.tenant_id, tenant_id),
        Eq(InstitutionWorkflowStage.workflow_key, instance.workflow_key),
        Eq(InstitutionWorkflowStage.workflow_version, instance.workflow_version),
        Eq(InstitutionWorkflowStage.stage_id, task.stage_id),
    )
    parallel_done = True
    if stage and stage.approval_mode == StageApprovalMode.PARALLEL:
        parallel_done = all(
            p.status in (ApprovalTaskStatus.APPROVED, ApprovalTaskStatus.CANCELLED) for p in peers if p.parallel_group == task.parallel_group
        )
    else:
        parallel_done = all(p.status in (ApprovalTaskStatus.APPROVED, ApprovalTaskStatus.CANCELLED) for p in peers)
    if parallel_done:
        next_order = task.stage_order + 1
        if await _spawn_stage_tasks(instance, next_order):
            await _history(tenant_id, instance.instance_id, "notification", "Approval notification queued", actor_id=user.id)
        else:
            instance.status = WorkflowInstanceStatus.APPROVED
            instance.completed_at = utcnow()
            instance.updated_at = utcnow()
            await instance.save()
            await _history(tenant_id, instance.instance_id, "completed", "Workflow approved", actor_id=user.id)
    await append_institution_audit(
        tenant_id,
        actor_id=user.id,
        action="workflow.task.approve",
        module="workflow",
        resource_type="approval_task",
        resource_id=task_id,
        metadata={"instance_id": instance.instance_id},
    )
    return _task_read(task)


async def reject_task(scope: AccessScope, user: User, task_id: str, payload: ApprovalReject) -> ApprovalTaskRead:
    authorize(scope, Permission.WORKFLOW_ADMIN_APPROVE)
    tenant_id = require_college_tenant_scope(scope)
    task = await InstitutionApprovalTask.find_one(
        Eq(InstitutionApprovalTask.tenant_id, tenant_id),
        Eq(InstitutionApprovalTask.task_id, task_id),
    )
    if task is None:
        raise AppError(code="NOT_FOUND", message="Approval task not found", status_code=404)
    instance = await InstitutionWorkflowInstance.find_one(
        Eq(InstitutionWorkflowInstance.tenant_id, tenant_id),
        Eq(InstitutionWorkflowInstance.instance_id, task.instance_id),
    )
    definition = await InstitutionWorkflowDefinition.find_one(
        Eq(InstitutionWorkflowDefinition.tenant_id, tenant_id),
        Eq(InstitutionWorkflowDefinition.workflow_key, instance.workflow_key),
        Eq(InstitutionWorkflowDefinition.version, instance.workflow_version),
    )
    await _can_act_on_task(scope, user, task, instance, definition)
    task.status = ApprovalTaskStatus.REJECTED
    task.acted_by_user_id = user.id
    task.comment = payload.reason
    task.completed_at = utcnow()
    await task.save()
    instance.status = WorkflowInstanceStatus.REJECTED
    instance.completed_at = utcnow()
    await instance.save()
    await _history(tenant_id, instance.instance_id, "rejected", payload.reason, actor_id=user.id, task_id=task_id)
    await append_institution_audit(
        tenant_id,
        actor_id=user.id,
        action="workflow.task.reject",
        module="workflow",
        resource_type="approval_task",
        resource_id=task_id,
        outcome="failure",
        metadata={"reason": payload.reason},
    )
    return _task_read(task)


async def request_additional_info(
    scope: AccessScope,
    user: User,
    task_id: str,
    payload: ApprovalInfoRequest,
) -> ApprovalTaskRead:
    authorize(scope, Permission.WORKFLOW_ADMIN_APPROVE)
    tenant_id = require_college_tenant_scope(scope)
    task = await InstitutionApprovalTask.find_one(
        Eq(InstitutionApprovalTask.tenant_id, tenant_id),
        Eq(InstitutionApprovalTask.task_id, task_id),
    )
    instance = await InstitutionWorkflowInstance.find_one(
        Eq(InstitutionWorkflowInstance.tenant_id, tenant_id),
        Eq(InstitutionWorkflowInstance.instance_id, task.instance_id),
    )
    definition = await InstitutionWorkflowDefinition.find_one(
        Eq(InstitutionWorkflowDefinition.tenant_id, tenant_id),
        Eq(InstitutionWorkflowDefinition.workflow_key, instance.workflow_key),
        Eq(InstitutionWorkflowDefinition.version, instance.workflow_version),
    )
    await _can_act_on_task(scope, user, task, instance, definition)
    task.status = ApprovalTaskStatus.INFO_REQUESTED
    task.comment = payload.message
    task.acted_by_user_id = user.id
    task.completed_at = utcnow()
    await task.save()
    instance.status = WorkflowInstanceStatus.INFO_REQUESTED
    await instance.save()
    await _history(tenant_id, instance.instance_id, "info_requested", payload.message, actor_id=user.id, task_id=task_id)
    return _task_read(task)


async def cancel_workflow_instance(scope: AccessScope, user: User, instance_id: str) -> WorkflowInstanceRead:
    authorize(scope, Permission.WORKFLOW_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    instance = await InstitutionWorkflowInstance.find_one(
        Eq(InstitutionWorkflowInstance.tenant_id, tenant_id),
        Eq(InstitutionWorkflowInstance.instance_id, instance_id),
    )
    if instance is None:
        raise AppError(code="NOT_FOUND", message="Workflow instance not found", status_code=404)
    definition = await InstitutionWorkflowDefinition.find_one(
        Eq(InstitutionWorkflowDefinition.tenant_id, tenant_id),
        Eq(InstitutionWorkflowDefinition.workflow_key, instance.workflow_key),
        Eq(InstitutionWorkflowDefinition.version, instance.workflow_version),
    )
    if not definition or not definition.cancellation_allowed:
        raise AppError(code="FORBIDDEN", message="Cancellation not allowed", status_code=403)
    if instance.requester_id != user.id and not _has_permission(scope, Permission.WORKFLOW_ADMIN_MANAGE.value):
        raise AppError(code="FORBIDDEN", message="Cannot cancel this workflow", status_code=403)
    instance.status = WorkflowInstanceStatus.CANCELLED
    instance.cancelled_at = utcnow()
    await instance.save()
    tasks = await InstitutionApprovalTask.find(
        Eq(InstitutionApprovalTask.tenant_id, tenant_id),
        Eq(InstitutionApprovalTask.instance_id, instance_id),
        Eq(InstitutionApprovalTask.status, ApprovalTaskStatus.PENDING),
    ).to_list()
    for t in tasks:
        t.status = ApprovalTaskStatus.CANCELLED
        await t.save()
    await _history(tenant_id, instance_id, "cancelled", "Workflow cancelled", actor_id=user.id)
    return _instance_read(instance)


async def resubmit_workflow_instance(scope: AccessScope, user: User, instance_id: str) -> WorkflowInstanceRead:
    authorize(scope, Permission.WORKFLOW_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    old = await InstitutionWorkflowInstance.find_one(
        Eq(InstitutionWorkflowInstance.tenant_id, tenant_id),
        Eq(InstitutionWorkflowInstance.instance_id, instance_id),
    )
    if old is None:
        raise AppError(code="NOT_FOUND", message="Workflow instance not found", status_code=404)
    definition = await InstitutionWorkflowDefinition.find_one(
        Eq(InstitutionWorkflowDefinition.tenant_id, tenant_id),
        Eq(InstitutionWorkflowDefinition.workflow_key, old.workflow_key),
        Eq(InstitutionWorkflowDefinition.version, old.workflow_version),
    )
    if not definition or not definition.resubmission_allowed:
        raise AppError(code="FORBIDDEN", message="Resubmission not allowed", status_code=403)
    if old.status not in (WorkflowInstanceStatus.REJECTED, WorkflowInstanceStatus.INFO_REQUESTED, WorkflowInstanceStatus.CANCELLED):
        raise AppError(code="VALIDATION_ERROR", message="Instance is not resubmittable", status_code=422)
    return await start_workflow_instance(
        scope,
        user,
        WorkflowInstanceStart(
            workflow_key=old.workflow_key,
            resource_type=old.resource_type,
            resource_id=old.resource_id,
            context={**old.context, "resubmission_of": instance_id},
        ),
    )


async def create_delegation(scope: AccessScope, user: User, payload: WorkflowDelegationCreate) -> WorkflowDelegationRead:
    authorize(scope, Permission.WORKFLOW_ADMIN_DELEGATE)
    tenant_id = require_college_tenant_scope(scope)
    delegatee = to_object_id(payload.delegatee_user_id, "delegatee_user_id")
    if delegatee == user.id:
        raise AppError(code="VALIDATION_ERROR", message="Cannot delegate to yourself", status_code=422)
    if payload.valid_until <= utcnow():
        raise AppError(code="VALIDATION_ERROR", message="valid_until must be in the future", status_code=422)
    did = payload.delegation_id.strip()
    if await InstitutionWorkflowDelegation.find_one(
        Eq(InstitutionWorkflowDelegation.tenant_id, tenant_id),
        Eq(InstitutionWorkflowDelegation.delegation_id, did),
    ):
        raise AppError(code="CONFLICT", message="Delegation id exists", status_code=409)
    doc = InstitutionWorkflowDelegation(
        tenant_id=tenant_id,
        delegation_id=did,
        delegator_user_id=user.id,
        delegatee_user_id=delegatee,
        workflow_keys=[k.strip().lower() for k in payload.workflow_keys],
        valid_until=payload.valid_until,
        created_by=user.id,
    )
    await doc.insert()
    await append_institution_audit(
        tenant_id,
        actor_id=user.id,
        action="workflow.delegation.create",
        module="workflow",
        resource_type="delegation",
        resource_id=did,
    )
    return WorkflowDelegationRead(
        delegation_id=doc.delegation_id,
        delegator_user_id=str(doc.delegator_user_id),
        delegatee_user_id=str(doc.delegatee_user_id),
        workflow_keys=doc.workflow_keys,
        valid_until=doc.valid_until,
        active=doc.active,
    )


async def list_workflow_history(scope: AccessScope, instance_id: str) -> list[ApprovalHistoryItem]:
    authorize(scope, Permission.WORKFLOW_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    rows = await InstitutionApprovalHistory.find(
        Eq(InstitutionApprovalHistory.tenant_id, tenant_id),
        Eq(InstitutionApprovalHistory.instance_id, instance_id),
    ).sort("-created_at").to_list()
    return [
        ApprovalHistoryItem(
            instance_id=r.instance_id,
            task_id=r.task_id,
            event=r.event,
            actor_id=str(r.actor_id) if r.actor_id else None,
            summary=r.summary,
            created_at=r.created_at,
        )
        for r in rows
    ]


async def list_escalations(scope: AccessScope, instance_id: str | None = None) -> list[WorkflowEscalationRead]:
    authorize(scope, Permission.WORKFLOW_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    query = InstitutionWorkflowEscalation.find(Eq(InstitutionWorkflowEscalation.tenant_id, tenant_id))
    if instance_id:
        query = query.find(Eq(InstitutionWorkflowEscalation.instance_id, instance_id))
    docs = await query.sort("-created_at").limit(50).to_list()
    return [
        WorkflowEscalationRead(
            escalation_id=d.escalation_id,
            instance_id=d.instance_id,
            task_id=d.task_id,
            reason=d.reason,
            created_at=d.created_at,
        )
        for d in docs
    ]


async def process_escalations(scope: AccessScope) -> dict:
    """Escalate overdue pending tasks (admin maintenance)."""
    authorize(scope, Permission.WORKFLOW_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    overdue = await InstitutionApprovalTask.find(
        Eq(InstitutionApprovalTask.tenant_id, tenant_id),
        Eq(InstitutionApprovalTask.status, ApprovalTaskStatus.PENDING),
    ).to_list()
    escalated = 0
    for task in overdue:
        if task.deadline_at is None or task.deadline_at > now:
            continue
        stage = await InstitutionWorkflowStage.find_one(
            Eq(InstitutionWorkflowStage.tenant_id, tenant_id),
            Eq(InstitutionWorkflowStage.stage_id, task.stage_id),
        )
        if not stage or not stage.escalation_permission:
            continue
        task.status = ApprovalTaskStatus.ESCALATED
        await task.save()
        esc_id = f"esc_{uuid4().hex[:10]}"
        await InstitutionWorkflowEscalation(
            tenant_id=tenant_id,
            escalation_id=esc_id,
            instance_id=task.instance_id,
            task_id=task.task_id,
            reason="deadline_exceeded",
            escalated_to_permission=stage.escalation_permission,
        ).insert()
        await InstitutionApprovalTask(
            tenant_id=tenant_id,
            task_id=f"tsk_{uuid4().hex[:12]}",
            instance_id=task.instance_id,
            stage_id=task.stage_id,
            stage_order=task.stage_order,
            parallel_group=task.parallel_group,
            assignee_permission=stage.escalation_permission,
            deadline_at=now + timedelta(hours=stage.deadline_hours or 24),
        ).insert()
        escalated += 1
    return {"escalated": escalated}