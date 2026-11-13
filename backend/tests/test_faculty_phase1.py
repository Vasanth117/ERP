"""Faculty phase 1 — dashboard and profile."""

from datetime import date, datetime, time, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.schemas import Pagination
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.models import (
    AcademicYearContext,
    PendingAttendanceSubmission,
    TimetableEntry,
)
from app.modules.auth.models import User
from app.modules.faculty.dashboard_service import get_dashboard_statistics, get_faculty_dashboard
from app.modules.faculty.enums import AssignmentRole, AssignmentStatus
from app.modules.faculty.models import FacultyAssignment, FacultyProfile
from app.modules.faculty.policy import require_faculty_scope
from app.modules.faculty.profile_service import get_faculty_profile, update_faculty_profile
from app.modules.faculty.schemas import FacultyProfileUpdate
from app.modules.tenants.models import Department, Tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
        await connect_redis()
    except Exception as exc:
        pytest.skip(f"Dependencies not available: {exc}")
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_redis()
    await close_mongo()


async def _seed_faculty(suffix: str) -> tuple[Tenant, Department, User, AccessScope]:
    tenant = Tenant(name=f"College {suffix}", code=f"c_{suffix}")
    await tenant.insert()
    department = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await department.insert()
    user = User(
        email=f"faculty+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Dr. Faculty",
        role=Role.FACULTY,
        tenant_id=tenant.id,
        department_id=department.id,
    )
    await user.insert()
    scope = AccessScope(
        role=Role.FACULTY,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=department.id,
        effective_permissions=permissions_for_role(Role.FACULTY),
    )
    return tenant, department, user, scope


@pytest.mark.anyio
async def test_faculty_profile_lazy_create(db_ready) -> None:
    _, _, user, scope = await _seed_faculty(uuid4().hex[:8])
    profile = await get_faculty_profile(scope, user)
    assert profile.email == user.email
    stored = await FacultyProfile.find_one({"user_id": user.id})
    assert stored is not None


@pytest.mark.anyio
async def test_permitted_profile_update(db_ready) -> None:
    _, _, user, scope = await _seed_faculty(uuid4().hex[:8])
    updated = await update_faculty_profile(
        scope,
        user,
        FacultyProfileUpdate(contact_phone="+911111111111", bio="Updated bio"),
    )
    assert updated.contact_phone == "+911111111111"
    assert updated.bio == "Updated bio"


@pytest.mark.anyio
async def test_non_faculty_forbidden(db_ready) -> None:
    tenant = Tenant(name="College", code=f"nc_{uuid4().hex[:6]}")
    await tenant.insert()
    admin = User(
        email=f"admin+{uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    with pytest.raises(AppError) as exc:
        require_faculty_scope(scope)
    assert exc.value.code == "FORBIDDEN"


@pytest.mark.anyio
async def test_cross_tenant_user_mismatch(db_ready) -> None:
    _, _, _, scope_a = await _seed_faculty(uuid4().hex[:8])
    tenant_b = Tenant(name="Other", code=f"oth_{uuid4().hex[:6]}")
    await tenant_b.insert()
    other = User(
        email=f"other+{uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Other",
        role=Role.FACULTY,
        tenant_id=tenant_b.id,
    )
    await other.insert()
    with pytest.raises(AppError) as exc:
        await get_faculty_profile(scope_a, other)
    assert exc.value.code == "FORBIDDEN"


@pytest.mark.anyio
async def test_dashboard_aggregation(db_ready) -> None:
    tenant, _, user, scope = await _seed_faculty(uuid4().hex[:8])
    await AcademicYearContext(
        tenant_id=tenant.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        is_current=True,
    ).insert()
    await FacultyAssignment(
        tenant_id=tenant.id,
        user_id=user.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        course_code="CS101",
        course_name="Data Structures",
        section="A",
        assignment_role=AssignmentRole.PRIMARY,
        status=AssignmentStatus.ACTIVE,
    ).insert()
    await TimetableEntry(
        tenant_id=tenant.id,
        faculty_user_id=user.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        day_of_week=date.today().weekday(),
        start_time=time(9, 0),
        end_time=time(10, 0),
        course_code="CS101",
        course_name="Data Structures",
        section="A",
    ).insert()
    await PendingAttendanceSubmission(
        tenant_id=tenant.id,
        faculty_user_id=user.id,
        class_label="B.Tech II",
        section="A",
        session_date=date.today(),
        due_at=datetime.now(timezone.utc),
    ).insert()

    dashboard = await get_faculty_dashboard(scope, user)
    assert dashboard.academic_term.academic_year_label == "2025-26"
    assert len(dashboard.assigned_courses) == 1
    assert len(dashboard.pending_attendance) == 1
    assert len(dashboard.timetable_today) >= 1

    stats = await get_dashboard_statistics(scope, user)
    assert stats.pending_task_count >= 1
    assert stats.classes_today >= 1


@pytest.mark.anyio
async def test_assignment_retrieval_read_only(db_ready) -> None:
    tenant, _, user, scope = await _seed_faculty(uuid4().hex[:8])
    doc = FacultyAssignment(
        tenant_id=tenant.id,
        user_id=user.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        course_code="CS101",
        course_name="Algorithms",
        section="B",
        allocation_locked=True,
        status=AssignmentStatus.ACTIVE,
    )
    await doc.insert()
    from app.modules.faculty.profile_service import get_assignment_history

    page = await get_assignment_history(scope, user, Pagination(limit=10, offset=0))
    assert page.total == 1
    assert page.items[0].allocation_locked is True


def test_profile_update_schema_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        FacultyProfileUpdate.model_validate({"employee_id": "E-999", "designation": "Professor"})
