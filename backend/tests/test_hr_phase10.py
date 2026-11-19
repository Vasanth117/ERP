"""HR staff portal phase 10 — settings, policies, audit and access."""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.schemas import Pagination
from app.common.time import utcnow
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.college_admin.models import InstitutionCampus
from app.modules.college_admin.security_admin_models import InstitutionAuditLog
from app.modules.hr.hr_audit_schemas import AuditExportRequest, HrAuditSearch, TemporaryAccessCreate
from app.modules.hr.hr_audit_service import (
    approve_temporary_access,
    audit_dashboard,
    create_temporary_access,
    export_audit,
    search_audit,
)
from app.modules.hr.hr_settings_schemas import (
    GeneralSettingsUpsert,
    PolicyCategoryUpsert,
    PolicyTransition,
    PolicyUpsert,
)
from app.core.exceptions import AppError
from app.modules.hr.enums import HrAccessScopeKind
from app.modules.hr.hr_audit_schemas import AccessScopeAssignmentUpsert
from app.modules.hr.hr_audit_service import employee_audit_timeline, upsert_access_scope
from app.modules.hr.hr_settings_models import HrPolicyAcknowledgement
from app.modules.hr.hr_settings_service import (
    get_general_settings,
    get_policy,
    list_policy_acknowledgements,
    transition_policy,
    upsert_general_settings,
    upsert_policy,
    upsert_policy_category,
)
from app.modules.hr.enums import HrStaffActivityType
from app.modules.hr.operational_models import HrStaffActivityLog
from app.modules.tenants.models import Department, Tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
    except Exception as exc:
        pytest.skip(f"MongoDB not available: {exc}")
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_mongo()


def _scope(user: User, role: Role) -> AccessScope:
    return AccessScope(
        role=role,
        user_id=user.id,
        tenant_id=user.tenant_id,
        department_id=None,
        effective_permissions=permissions_for_role(role),
    )


async def _seed(suffix: str):
    tenant = Tenant(name=f"HR10 {suffix}", code=f"hr10_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="HR", code=f"HR-{suffix}")
    await dept.insert()
    campus = InstitutionCampus(tenant_id=tenant.id, campus_code=f"C{suffix}", name="Main", is_main=True)
    await campus.insert()
    hr_user = User(
        email=f"hr10+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="HR Staff",
        role=Role.HR_STAFF,
        tenant_id=tenant.id,
    )
    await hr_user.insert()
    approver = User(
        email=f"hr10a+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="HR Approver",
        role=Role.HR_STAFF,
        tenant_id=tenant.id,
    )
    await approver.insert()
    for user in (hr_user, approver):
        await EmployeeRecord(
            tenant_id=tenant.id,
            user_id=user.id,
            department_id=dept.id,
            campus_id=campus.id,
            employment_status=FacultyEmploymentStatus.ACTIVE,
        ).insert()
    return tenant, _scope(hr_user, Role.HR_STAFF), _scope(approver, Role.HR_STAFF), hr_user, approver


@pytest.mark.asyncio
async def test_settings_policy_lifecycle_and_audit(db_ready):
    suffix = uuid4().hex[:6]
    tenant, hr_scope, approver_scope, hr_user, approver = await _seed(suffix)
    await upsert_general_settings(
        hr_scope,
        GeneralSettingsUpsert(department_name="People Operations", contact_email="hr@example.edu"),
    )
    gs = await get_general_settings(hr_scope)
    assert gs.department_name == "People Operations"
    await upsert_policy_category(
        hr_scope,
        PolicyCategoryUpsert(category_code="leave", title="Leave Policies", sort_order=1),
    )
    policy = await upsert_policy(
        hr_scope,
        PolicyUpsert(
            policy_code=f"LV-{suffix}",
            category_code="leave",
            title="Annual leave",
            requires_acknowledgement=True,
            settings={"annual_entitlement": 24, "carry_forward_max": 10},
            change_summary="Initial version",
        ),
    )
    assert policy.status.value == "draft"
    for action in ("submit_review", "approve", "publish", "activate"):
        scope = approver_scope if action == "approve" else hr_scope
        policy = await transition_policy(scope, policy.id, PolicyTransition(action=action))
    assert policy.status.value == "active"
    acks = await list_policy_acknowledgements(hr_scope, policy.id)
    assert len(acks) >= 1
    await HrStaffActivityLog(
        tenant_id=tenant.id,
        activity_type=HrStaffActivityType.POLICY_CHANGE,
        summary="test activity",
        actor_id=hr_user.id,
    ).insert()
    await InstitutionAuditLog(
        tenant_id=tenant.id,
        actor_id=hr_user.id,
        action="hr.policy_change",
        module="hr",
        resource_type="hr_policy",
        resource_id=policy.policy_code,
        entry_hash="abc",
    ).insert()
    dash = await audit_dashboard(hr_scope)
    assert dash.total_activities >= 1
    assert dash.institution_audit_entries >= 1
    page = await search_audit(hr_scope, Pagination(limit=20, offset=0), HrAuditSearch(action_prefix="hr."))
    assert page.total >= 1
    export = await export_audit(hr_scope, AuditExportRequest(filters=HrAuditSearch()))
    assert export.row_count >= 1
    assert export.file_content_base64


@pytest.mark.asyncio
async def test_temporary_access_approval(db_ready):
    suffix = uuid4().hex[:6]
    tenant, hr_scope, approver_scope, hr_user, approver = await _seed(suffix)
    grant = await create_temporary_access(
        hr_scope,
        TemporaryAccessCreate(
            grant_code=f"TMP-{suffix}",
            subject_user_id=str(hr_user.id),
            granted_permissions=["hr:leave:manage"],
            reason="Cover leave admin",
            starts_at=utcnow(),
            expires_at=utcnow() + timedelta(days=2),
        ),
    )
    assert grant.status.value == "pending"
    approved = await approve_temporary_access(approver_scope, grant.id)
    assert approved.status.value in {"active", "approved"}


@pytest.mark.asyncio
async def test_tenant_isolation_and_access_scope(db_ready):
    suffix_a = uuid4().hex[:6]
    suffix_b = uuid4().hex[:6]
    _, scope_a, _, hr_a, approver_a = await _seed(suffix_a)
    _, scope_b, _, _, _ = await _seed(suffix_b)
    await upsert_policy_category(scope_a, PolicyCategoryUpsert(category_code="leave", title="Leave", sort_order=1))
    policy = await upsert_policy(
        scope_a,
        PolicyUpsert(policy_code=f"ISO-{suffix_a}", category_code="leave", title="Test", settings={}),
    )
    with pytest.raises(AppError):
        await get_policy(scope_b, policy.id)
    await upsert_access_scope(
        scope_a,
        AccessScopeAssignmentUpsert(
            user_id=str(hr_a.id),
            scope_kind=HrAccessScopeKind.EMPLOYEE_SET,
            employee_user_ids=[str(approver_a.id)],
        ),
    )
    with pytest.raises(AppError):
        await employee_audit_timeline(scope_a, str(hr_a.id), Pagination(limit=10, offset=0))