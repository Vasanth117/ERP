"""College Admin phase 1 — dashboard and institution settings."""

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
from app.modules.college_admin.dashboard_service import get_dashboard_overview, get_institutional_statistics
from app.modules.college_admin.enums import DashboardDateRange
from app.modules.college_admin.institution_service import (
    create_campus,
    get_institution_profile,
    get_institution_settings,
    update_institution_profile,
    update_institution_settings,
)
from app.modules.college_admin.schemas import CampusCreate, InstitutionProfileUpdate
from app.modules.college_admin.settings_registry import InstitutionSettingsUpdate, merge_institution_settings
from app.modules.students.models import StudentProfile
from app.modules.tenants.models import Department, Tenant
from app.modules.tenants.platform_models import InstitutionAddress


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


async def _seed_admin(suffix: str) -> tuple[Tenant, Department, User, AccessScope]:
    tenant = Tenant(
        name=f"College {suffix}",
        code=f"ca_{suffix}",
        institution_email=f"info+{suffix}@example.com",
        institution_type="university",
    )
    await tenant.insert()
    department = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await department.insert()
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
    return tenant, department, user, scope


@pytest.mark.anyio
async def test_dashboard_aggregation(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, department, user, scope = await _seed_admin(suffix)
    await AcademicYearContext(
        tenant_id=tenant.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        is_current=True,
    ).insert()
    student_user = User(
        email=f"student+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student One",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        department_id=department.id,
        is_active=True,
    )
    await student_user.insert()
    await StudentProfile(
        tenant_id=tenant.id,
        user_id=student_user.id,
        roll_number="21CSE001",
        programme_code="BTECH-CSE",
        department_id=department.id,
    ).insert()

    overview = await get_dashboard_overview(scope, user, date_range=DashboardDateRange.WEEK)
    assert overview.academic_term.academic_year_label == "2025-26"
    assert overview.statistics.total_students == 1
    assert overview.statistics.active_students == 1
    assert overview.statistics.department_count == 1
    assert overview.statistics.programme_count == 1

    stats = await get_institutional_statistics(scope)
    assert stats.statistics.faculty_count == 0


@pytest.mark.anyio
async def test_institution_profile_and_campus(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _department, _user, scope = await _seed_admin(suffix)
    profile = await get_institution_profile(scope)
    assert profile.tenant_code == tenant.code
    assert profile.legal_name == tenant.name

    updated = await update_institution_profile(
        scope,
        InstitutionProfileUpdate(display_name="Updated College", institution_code="INST001"),
    )
    assert updated.display_name == "Updated College"
    assert updated.institution_code == "INST001"

    main = await create_campus(
        scope,
        CampusCreate(campus_code="main", name="Main Campus", is_main=True, address=InstitutionAddress(city="City")),
    )
    assert main.campus_code == "MAIN"
    duplicate_scope = scope
    with pytest.raises(AppError) as dup_exc:
        await create_campus(duplicate_scope, CampusCreate(campus_code="main", name="Duplicate"))
    assert dup_exc.value.status_code == 409


@pytest.mark.anyio
async def test_settings_validation_and_tenant_isolation(db_ready) -> None:
    suffix_a = uuid4().hex[:8]
    suffix_b = uuid4().hex[:8]
    tenant_a, _, user_a, scope_a = await _seed_admin(suffix_a)
    tenant_b, _, _user_b, scope_b = await _seed_admin(suffix_b)

    settings = await get_institution_settings(scope_a)
    assert settings.tenant_id == str(tenant_a.id)

    await update_institution_settings(
        scope_a,
        InstitutionSettingsUpdate(timezone="Asia/Kolkata", locale="en-IN"),
    )
    with pytest.raises(ValueError):
        merge_institution_settings({}, {"tenant_code": "hacked"})

    scope_b_wrong = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=scope_b.user_id,
        tenant_id=tenant_b.id,
        department_id=None,
        effective_permissions=frozenset({Permission.INSTITUTION_PROFILE_READ}),
    )
    profile_b = await get_institution_profile(scope_b_wrong)
    assert profile_b.tenant_id == str(tenant_b.id)
    assert profile_b.tenant_id != str(tenant_a.id)


@pytest.mark.anyio
async def test_unauthorized_settings_permission(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, user, _scope = await _seed_admin(suffix)
    student = User(
        email=f"st+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    student_scope = AccessScope(
        role=Role.STUDENT,
        user_id=student.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.STUDENT),
    )
    with pytest.raises(AppError) as exc:
        await get_dashboard_overview(student_scope, student)
    assert exc.value.status_code == 403
