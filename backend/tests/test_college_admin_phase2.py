"""College Admin phase 2 — users, roles, and organization."""

from uuid import uuid4

import pytest

from app.authorization.permissions import Permission, permissions_for_role
from app.authorization.resolver import effective_permissions_for_user
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.common.ids import to_object_id
from app.core.security import hash_password
from beanie.odm.operators.find.comparison import Eq
from app.modules.auth.models import User
from app.modules.college_admin.identity_schemas import (
    InstitutionDepartmentCreate,
    InstitutionDepartmentUpdate,
    InstitutionRoleCreate,
    InstitutionUserCreate,
    InstitutionUserInvite,
    InvitationAccept,
    OrganizationUnitCreate,
    UserRoleAssign,
)
from app.modules.college_admin.organization_service import (
    create_institution_department,
    create_organization_unit,
    update_institution_department,
)
from app.modules.college_admin.rbac_policy import actor_may_assign_role
from app.modules.college_admin.role_management_service import create_institution_role, list_permissions
from app.modules.college_admin.user_management_dashboard_page_service import (
    get_user_management_dashboard_page,
)
from app.modules.college_admin.user_all_users_list_page_service import get_all_users_list_page
from app.modules.college_admin.user_details_page_service import get_user_details_page
from app.modules.college_admin.create_new_user_page_service import get_create_new_user_page
from app.modules.college_admin.edit_user_information_page_service import get_edit_user_information_page
from app.modules.college_admin.bulk_user_invitation_page_service import get_bulk_user_invitation_page
from app.modules.college_admin.role_management_dashboard_page_service import get_role_management_dashboard_page
from app.modules.college_admin.create_edit_role_page_service import (
    get_create_edit_role_page_by_id,
    save_create_edit_role,
)
from app.modules.college_admin.permission_management_page_service import (
    get_permission_management_page,
)
from app.modules.college_admin.role_assignment_page_service import get_role_assignment_page
from app.modules.college_admin.schemas import CreateEditRoleFormValues, CreateEditRoleSavePayload
from app.modules.college_admin.user_management_service import (
    accept_institution_invitation,
    create_institution_user,
    invite_institution_user,
    suspend_user,
)
from app.modules.tenants.models import Department, Tenant


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
    tenant = Tenant(name=f"College {suffix}", code=f"p2_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+{suffix}@example.com",
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
async def test_create_user_and_duplicate(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, scope = await _seed_admin(suffix)
    dept = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await dept.insert()
    created = await create_institution_user(
        scope,
        InstitutionUserCreate(
            email=f"faculty+{suffix}@example.com",
            password="password1234567890",
            full_name="Faculty Member",
            role=Role.FACULTY,
            department_id=str(dept.id),
        ),
    )
    assert created.role == Role.FACULTY

    dash = await get_user_management_dashboard_page(scope)
    assert dash.page_title == "User Management Dashboard"
    assert len(dash.kpis) == 4
    assert dash.kpis[0].value == "2"

    users_list = await get_all_users_list_page(scope)
    assert users_list.page_title == "All Users List"
    assert users_list.pagination.total >= 2

    details = await get_user_details_page(scope, to_object_id(created.user_id, "user id"))
    assert details.page_title == "User Details"
    assert details.profile_name == "Faculty Member"
    assert details.user_id == created.user_id
    assert len(details.account_fields) >= 4

    create_page = await get_create_new_user_page(scope)
    assert create_page.page_title == "Create New User"
    assert len(create_page.steps) == 3
    assert len(create_page.department_options) >= 2

    edit_page = await get_edit_user_information_page(scope, to_object_id(created.user_id, "user id"))
    assert edit_page.page_title == "Edit User Information"
    assert edit_page.form.full_name == "Faculty Member"

    bulk_page = await get_bulk_user_invitation_page(scope)
    assert bulk_page.page_title == "Bulk User Invitation"
    assert len(bulk_page.steps) == 4

    roles_dash = await get_role_management_dashboard_page(scope)
    assert roles_dash.page_title == "Role Management Dashboard"
    assert len(roles_dash.kpis) == 4

    create_role_page = await get_create_edit_role_page_by_id(scope, None)
    assert create_role_page.page_title == "Create / Edit Role"
    assert create_role_page.is_create is True
    assert len(create_role_page.permission_groups) >= 3

    saved_role_page = await save_create_edit_role(
        scope,
        CreateEditRoleSavePayload(
            role_id=None,
            form=CreateEditRoleFormValues(
                name="Examination Cell",
                role_code=f"EXAM_{suffix[:6].upper()}",
                base_role=Role.EXAMINATION_CELL.value,
                scope="whole_college",
                description="Plans examinations and results.",
                require_mfa=True,
                restrict_campus_network=True,
                time_bound_access=False,
            ),
            permission_toggles=[],
        ),
    )
    assert saved_role_page.role_id
    assert saved_role_page.form.name == "Examination Cell"

    perm_page = await get_permission_management_page(scope)
    assert perm_page.page_title == "Permission Management"
    assert len(perm_page.columns) == 8
    assert len(perm_page.groups) >= 5

    assign_page = await get_role_assignment_page(scope)
    assert assign_page.page_title == "Role Assignment"
    assert len(assign_page.recent_table_headers) == 5
    with pytest.raises(AppError) as exc:
        await create_institution_user(
            scope,
            InstitutionUserCreate(
                email=f"faculty+{suffix}@example.com",
                password="password1234567890",
                full_name="Dup",
                role=Role.FACULTY,
                department_id=str(dept.id),
            ),
        )
    assert exc.value.status_code == 409


@pytest.mark.anyio
async def test_privilege_escalation_blocked(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, scope = await _seed_admin(suffix)
    faculty_scope = AccessScope(
        role=Role.FACULTY,
        user_id=scope.user_id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.FACULTY),
    )
    with pytest.raises(AppError):
        await create_institution_user(
            faculty_scope,
            InstitutionUserCreate(
                email=f"x+{suffix}@example.com",
                password="password1234567890",
                full_name="X",
                role=Role.STUDENT,
            ),
        )
    with pytest.raises(AppError):
        actor_may_assign_role(Role.COLLEGE_ADMIN, Role.COLLEGE_ADMIN, has_privileged_grant=False)


@pytest.mark.anyio
async def test_invitation_accept_and_custom_role(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, scope = await _seed_admin(suffix)
    dept = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await dept.insert()
    custom = await create_institution_role(
        scope,
        InstitutionRoleCreate(
            role_code="LAB_MGR",
            name="Lab Manager",
            base_role=Role.FACULTY,
            granted_permissions=[Permission.FACULTY_LMS_MANAGE.value],
        ),
    )
    invite = await invite_institution_user(
        scope,
        InstitutionUserInvite(
            email=f"invite+{suffix}@example.com",
            full_name="Invited Faculty",
            role=Role.FACULTY,
            department_id=str(dept.id),
            institution_role_id=custom.role_id,
        ),
    )
    assert invite.accept_token is not None
    accepted = await accept_institution_invitation(
        InvitationAccept(token=invite.accept_token, password="password1234567890"),
    )
    assert accepted.email == f"invite+{suffix}@example.com"
    assert "LAB_MGR" in accepted.institution_roles
    invited_user = await User.find_one(Eq(User.email, f"invite+{suffix}@example.com"), Eq(User.tenant_id, tenant.id))
    perms = await effective_permissions_for_user(invited_user)
    assert Permission.FACULTY_LMS_MANAGE in perms


@pytest.mark.anyio
async def test_department_hierarchy_cycle_prevention(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, scope = await _seed_admin(suffix)
    await create_organization_unit(
        scope,
        OrganizationUnitCreate(unit_code="ENG", name="Engineering", unit_type="school"),
    )
    parent = await create_institution_department(
        scope,
        InstitutionDepartmentCreate(department_code="CSE", name="Computer Science"),
    )
    child = await create_institution_department(
        scope,
        InstitutionDepartmentCreate(
            department_code="IT",
            name="Information Tech",
            parent_department_id=parent.department_id,
        ),
    )
    with pytest.raises(AppError) as cycle_exc:
        await update_institution_department(
            scope,
            parent.department_id,
            InstitutionDepartmentUpdate(parent_department_id=child.department_id),
        )
    assert cycle_exc.value.status_code == 422


@pytest.mark.anyio
async def test_suspend_user_and_tenant_isolation(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant_a, admin_a, scope_a = await _seed_admin(suffix)
    suffix_b = uuid4().hex[:8]
    tenant_b, _, scope_b = await _seed_admin(suffix_b)
    target = await create_institution_user(
        scope_a,
        InstitutionUserCreate(
            email=f"student+{suffix}@example.com",
            password="password1234567890",
            full_name="Student",
            role=Role.STUDENT,
        ),
    )
    suspended = await suspend_user(scope_a, to_object_id(target.user_id, "user id"), reason="policy")
    assert suspended.account_status.value == "suspended"
    with pytest.raises(AppError):
        await suspend_user(scope_b, to_object_id(target.user_id, "user id"), reason="cross-tenant")


@pytest.mark.anyio
async def test_permissions_catalog_seeded(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, _, scope = await _seed_admin(suffix)
    perms = await list_permissions(scope)
    assert any(p.permission_code == Permission.FACULTY_DASHBOARD_READ.value for p in perms)
