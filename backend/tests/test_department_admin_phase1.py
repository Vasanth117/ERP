"""Department Admin phase 1 — dashboard and profile."""

from uuid import uuid4

import pytest

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.models import AcademicYearContext
from app.modules.auth.models import User
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.organization_service import create_institution_department
from app.modules.college_admin.identity_schemas import InstitutionDepartmentCreate
from app.modules.department_admin.dashboard_service import (
    get_department_dashboard_bundle,
    get_department_overview,
)
from app.modules.department_admin.profile_service import (
    create_profile_change_request,
    update_department_profile,
    upsert_department_setting,
)
from app.modules.department_admin.schemas import (
    DepartmentDashboardFilters,
    DepartmentProfileChangeRequestCreate,
    DepartmentProfileDetailsUpdate,
    DepartmentSettingUpdate,
)
from app.modules.students.models import StudentProfile
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
    from app.core.database import document_models

    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_redis()
    await close_mongo()


async def _seed_department_admin(suffix: str) -> tuple[Tenant, Department, InstitutionDepartment, User, AccessScope]:
    tenant = Tenant(
        name=f"College {suffix}",
        code=f"dept_{suffix}",
        institution_email=f"info+{suffix}@example.com",
        institution_type="university",
    )
    await tenant.insert()
    central = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await central.insert()
    college_admin = User(
        email=f"cadmin+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await college_admin.insert()
    admin_scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=college_admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    institution = await create_institution_department(
        admin_scope,
        InstitutionDepartmentCreate(department_code="CSE", name="Computer Science", programme_codes=["BTECH-CSE"]),
    )
    from beanie import PydanticObjectId

    inst_doc = await InstitutionDepartment.get(PydanticObjectId(institution.department_id))
    assert inst_doc is not None
    dept_admin = User(
        email=f"deptadmin+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Dept Admin",
        role=Role.DEPARTMENT_ADMIN,
        tenant_id=tenant.id,
        department_id=central.id,
        is_active=True,
    )
    await dept_admin.insert()
    scope = AccessScope(
        role=Role.DEPARTMENT_ADMIN,
        user_id=dept_admin.id,
        tenant_id=tenant.id,
        department_id=central.id,
        effective_permissions=permissions_for_role(Role.DEPARTMENT_ADMIN),
    )
    return tenant, central, inst_doc, dept_admin, scope


@pytest.mark.anyio
async def test_department_dashboard_overview(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, central, _inst, user, scope = await _seed_department_admin(suffix)
    await AcademicYearContext(
        tenant_id=tenant.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        is_current=True,
    ).insert()
    student_user = User(
        email=f"student+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        department_id=central.id,
        is_active=True,
    )
    await student_user.insert()
    await StudentProfile(
        tenant_id=tenant.id,
        user_id=student_user.id,
        roll_number=f"R{suffix}",
        programme_code="BTECH-CSE",
        batch_label="2024",
        section_code="A",
        department_id=central.id,
    ).insert()

    overview = await get_department_overview(scope, user, filters=DepartmentDashboardFilters())
    assert overview.department_code == "CSE"
    assert overview.total_active_students == 1
    assert overview.programme_count == 1

    bundle = await get_department_dashboard_bundle(scope, user)
    assert bundle.students.total_enrolled == 1
    assert bundle.overview.college_name == tenant.name


@pytest.mark.anyio
async def test_department_profile_and_settings(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _tenant, _central, _inst, user, scope = await _seed_department_admin(suffix)
    updated = await update_department_profile(
        scope,
        user,
        DepartmentProfileDetailsUpdate(description="Department overview", contact_email="cse@example.com"),
    )
    assert updated.description == "Department overview"
    setting = await upsert_department_setting(
        scope,
        user,
        "attendance_alert_enabled",
        DepartmentSettingUpdate(value=True),
    )
    assert setting.value is True


@pytest.mark.anyio
async def test_department_isolation_and_role_denied(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, central, _inst, user, scope = await _seed_department_admin(suffix)
    other_central = Department(tenant_id=tenant.id, name="ECE", code="ECE")
    await other_central.insert()
    other_admin = User(
        email=f"other+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Other Dept",
        role=Role.DEPARTMENT_ADMIN,
        tenant_id=tenant.id,
        department_id=other_central.id,
    )
    await other_admin.insert()
    student_other = User(
        email=f"student2+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Other Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        department_id=other_central.id,
        is_active=True,
    )
    await student_other.insert()
    await StudentProfile(
        tenant_id=tenant.id,
        user_id=student_other.id,
        roll_number=f"X{suffix}",
        programme_code="BTECH-ECE",
        department_id=other_central.id,
    ).insert()

    overview = await get_department_overview(scope, user)
    assert overview.total_active_students == 0

    faculty = User(
        email=f"faculty+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Faculty",
        role=Role.FACULTY,
        tenant_id=tenant.id,
        department_id=central.id,
    )
    await faculty.insert()
    faculty_scope = AccessScope(
        role=Role.FACULTY,
        user_id=faculty.id,
        tenant_id=tenant.id,
        department_id=central.id,
        effective_permissions=permissions_for_role(Role.FACULTY),
    )
    with pytest.raises(AppError) as exc:
        await get_department_overview(faculty_scope, faculty)
    assert exc.value.status_code == 403

    await create_profile_change_request(
        scope,
        user,
        DepartmentProfileChangeRequestCreate(field_name="name", proposed_value="Computer Science Dept"),
    )