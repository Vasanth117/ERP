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
