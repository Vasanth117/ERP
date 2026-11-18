"""College Admin phase 9 — workflow and security administration."""

from datetime import timedelta
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.time import utcnow
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.security_admin_service import (
    append_institution_audit,
    export_audit_records,
    record_login_activity,
    search_institution_audit_logs,
    verify_audit_integrity,
)
from app.modules.college_admin.security_admin_schemas import AuditLogSearch
from app.modules.college_admin.workflow_admin_models import WorkflowInstanceStatus
from app.modules.college_admin.workflow_admin_schemas import (
    ApprovalDecision,
    WorkflowDefinitionUpsert,
    WorkflowInstanceStart,
    WorkflowStageUpsert,
)
from app.modules.college_admin.workflow_admin_service import (
    approve_task,
    create_delegation,
    list_pending_approval_tasks,
    reject_task,
    start_workflow_instance,
    upsert_workflow_definition,
)
from app.common.schemas import Pagination
from app.modules.college_admin.workflow_admin_schemas import WorkflowDelegationCreate
from app.modules.tenants.models import Tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
    except Exception as exc:
        pytest.skip(f"MongoDB not available: {exc}")
    try:
        await connect_redis()
    except Exception:
        pass
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_redis()
    await close_mongo()


async def _seed_admin(suffix: str) -> tuple[Tenant, User, AccessScope]:
    tenant = Tenant(name=f"College P9 {suffix}", code=f"p9_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+p9+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await user.insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    return tenant, user, scope


@pytest.mark.anyio
async def test_sequential_workflow_approval(db_ready):
    tenant, user, scope = await _seed_admin(uuid4().hex[:6])
    await upsert_workflow_definition(
        scope,
        user,
        WorkflowDefinitionUpsert(
            workflow_key="procurement_test",
            title="Procurement",
            allow_self_approval=True,
            stages=[
                WorkflowStageUpsert(
                    stage_id="step1",
                    stage_order=1,
                    title="First",
                    assignee_permission=Permission.WORKFLOW_ADMIN_APPROVE.value,
                ),
                WorkflowStageUpsert(
                    stage_id="step2",
                    stage_order=2,
                    title="Second",
                    assignee_permission=Permission.WORKFLOW_ADMIN_APPROVE.value,
                ),
            ],
        ),
    )
    instance = await start_workflow_instance(
        scope,
        user,
        WorkflowInstanceStart(workflow_key="procurement_test", resource_type="procurement", resource_id="po-1"),
    )
    pending = await list_pending_approval_tasks(scope, Pagination(limit=20, offset=0))
    assert pending.total >= 1
    task1 = pending.items[0]
    await approve_task(scope, user, task1.task_id, ApprovalDecision(comment="ok"))
    pending2 = await list_pending_approval_tasks(scope, Pagination(limit=20, offset=0))
    assert pending2.total >= 1
    await approve_task(scope, user, pending2.items[0].task_id, ApprovalDecision())
    from app.modules.college_admin.workflow_admin_models import InstitutionWorkflowInstance

    done = await InstitutionWorkflowInstance.find_one(
        Eq(InstitutionWorkflowInstance.tenant_id, tenant.id),
        Eq(InstitutionWorkflowInstance.instance_id, instance.instance_id),
    )
    assert done.status == WorkflowInstanceStatus.APPROVED


@pytest.mark.anyio
async def test_self_approval_blocked(db_ready):
    tenant, requester, scope = await _seed_admin(uuid4().hex[:6])
    await upsert_workflow_definition(
        scope,
        requester,
        WorkflowDefinitionUpsert(
            workflow_key="leave_self",
            title="Leave",
            allow_self_approval=False,
            stages=[
                WorkflowStageUpsert(
                    stage_id="only",
                    stage_order=1,
                    title="Approver",
                    assignee_permission=Permission.WORKFLOW_ADMIN_APPROVE.value,
                ),
            ],
        ),
    )
    await start_workflow_instance(
        scope,
        requester,
        WorkflowInstanceStart(workflow_key="leave_self", resource_type="leave", resource_id="lr-1"),
    )
    pending = await list_pending_approval_tasks(scope, Pagination(limit=5, offset=0))
    with pytest.raises(AppError) as exc:
        await approve_task(scope, requester, pending.items[0].task_id, ApprovalDecision())
    assert exc.value.status_code == 403


@pytest.mark.anyio
async def test_unauthorized_approval(db_ready):
    tenant = Tenant(name="P9 dept", code="p9dept")
    await tenant.insert()
    dept_user = User(
        email=f"dept+{uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Dept",
        role=Role.DEPARTMENT_ADMIN,
        tenant_id=tenant.id,
    )
    await dept_user.insert()
    admin = User(
        email=f"admin+{uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    admin_scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    dept_scope = AccessScope(
        role=Role.DEPARTMENT_ADMIN,
        user_id=dept_user.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.DEPARTMENT_ADMIN),
    )
    await upsert_workflow_definition(
        admin_scope,
        admin,
        WorkflowDefinitionUpsert(
            workflow_key="finance_wf",
            title="Finance",
            stages=[
                WorkflowStageUpsert(
                    stage_id="fin",
                    stage_order=1,
                    title="Finance",
                    assignee_permission=Permission.FINANCE_ADMIN_APPROVE.value,
                ),
            ],
        ),
    )
    await start_workflow_instance(
        admin_scope,
        admin,
        WorkflowInstanceStart(workflow_key="finance_wf", resource_type="payment", resource_id="pay-1"),
    )
    pending = await list_pending_approval_tasks(admin_scope, Pagination(limit=5, offset=0))
    with pytest.raises(AppError) as exc:
        await approve_task(dept_scope, dept_user, pending.items[0].task_id, ApprovalDecision())
    assert exc.value.status_code == 403


@pytest.mark.anyio
async def test_delegation_approval(db_ready):
    tenant, admin, admin_scope = await _seed_admin(uuid4().hex[:6])
    delegate = User(
        email=f"delegate+{uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Delegate",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await delegate.insert()
    delegate_scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=delegate.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    await upsert_workflow_definition(
        admin_scope,
        admin,
        WorkflowDefinitionUpsert(
            workflow_key="deleg_wf",
            title="Deleg",
            stages=[
                WorkflowStageUpsert(
                    stage_id="one",
                    stage_order=1,
                    title="One",
                    assignee_permission=Permission.HR_ADMIN_LEAVE_APPROVE.value,
                ),
            ],
        ),
    )
    await create_delegation(
        admin_scope,
        admin,
        WorkflowDelegationCreate(
            delegation_id=f"del_{uuid4().hex[:6]}",
            delegatee_user_id=str(delegate.id),
            workflow_keys=["deleg_wf"],
            valid_until=utcnow() + timedelta(days=7),
        ),
    )
    await start_workflow_instance(
        admin_scope,
        admin,
        WorkflowInstanceStart(workflow_key="deleg_wf", resource_type="leave", resource_id="lv-deleg"),
    )
    pending = await list_pending_approval_tasks(delegate_scope, Pagination(limit=5, offset=0))
    assert pending.total >= 1
    await approve_task(delegate_scope, delegate, pending.items[0].task_id, ApprovalDecision(comment="delegated ok"))


@pytest.mark.anyio
async def test_audit_integrity_and_tenant_isolation(db_ready):
    t1, user1, scope1 = await _seed_admin(uuid4().hex[:6])
    t2, _, scope2 = await _seed_admin(uuid4().hex[:6])
    await append_institution_audit(
        t1.id,
        actor_id=user1.id,
        action="test.action",
        module="security",
        resource_type="test",
        resource_id="1",
    )
    integrity = await verify_audit_integrity(scope1)
    assert integrity.valid is True
    page = await search_institution_audit_logs(scope1, AuditLogSearch(module="security"), Pagination(limit=10, offset=0))
    assert page.total >= 1
    page2 = await search_institution_audit_logs(scope2, AuditLogSearch(), Pagination(limit=10, offset=0))
    assert all(item.module != "security" or item.action != "test.action" for item in page2.items) or page2.total == 0


@pytest.mark.anyio
async def test_login_activity_and_export(db_ready):
    tenant, user, scope = await _seed_admin(uuid4().hex[:6])
    await record_login_activity(tenant.id, user_id=user.id, email=user.email, success=False, failure_reason="bad_password")
    await append_institution_audit(
        tenant.id,
        actor_id=user.id,
        action="auth.login.failure",
        module="auth",
        resource_type="user",
        resource_id=str(user.id),
    )
    export = await export_audit_records(scope, user, AuditLogSearch(action_prefix="auth"))
    assert export.record_count >= 1