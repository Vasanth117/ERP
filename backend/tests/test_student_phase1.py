"""Student phase 1 — dashboard, profile, and academic enrollment."""

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
from app.modules.academics.curriculum_models import EnrollmentRosterEntry
from app.modules.academics.models import AcademicYearContext, TimetableEntry
from app.modules.auth.models import User
from app.modules.students.academic_service import get_academic_details, submit_enrollment_request
from app.modules.students.dashboard_service import get_dashboard_statistics, get_student_dashboard
from app.modules.students.enums import StudentAcademicRequestType
from app.modules.students.models import StudentAcademicRecord, StudentProfile
from app.modules.students.policy import require_student_scope
from app.modules.students.profile_service import get_student_profile, update_student_profile
from app.modules.students.schemas import EnrollmentRequestCreate, StudentProfileUpdate
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


async def _seed_student(suffix: str) -> tuple[Tenant, Department, User, AccessScope]:
    tenant = Tenant(name=f"College {suffix}", code=f"sc_{suffix}")
    await tenant.insert()
    department = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await department.insert()
    user = User(
        email=f"student+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Alex Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        department_id=department.id,
    )
    await user.insert()
    scope = AccessScope(
        role=Role.STUDENT,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=department.id,
        effective_permissions=permissions_for_role(Role.STUDENT),
    )
    return tenant, department, user, scope


async def _seed_academic_context(tenant: Tenant, user: User) -> None:
    await AcademicYearContext(
        tenant_id=tenant.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        is_current=True,
    ).insert()
    await EnrollmentRosterEntry(
        tenant_id=tenant.id,
        course_id="cse101",
        course_code="CSE101",
        section_code="A",
        student_user_id=user.id,
        roll_number="21CSE001",
        display_name="Alex Student",
        academic_year_label="2025-26",
        semester_label="Odd",
    ).insert()
    await TimetableEntry(
        tenant_id=tenant.id,
        faculty_user_id=user.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(10, 0),
        course_code="CSE101",
        course_name="Programming",
        section="A",
        room="LH-1",
    ).insert()
    profile = await StudentProfile.find_one({"user_id": user.id})
    if profile:
        profile.student_id = "STU-001"
        profile.roll_number = "21CSE001"
        profile.programme_code = "BTECH-CSE"
        profile.programme_name = "B.Tech CSE"
        profile.batch_label = "2021"
        profile.section_code = "A"
        await profile.save()
    await StudentAcademicRecord(
        tenant_id=tenant.id,
        user_id=user.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        fee_snapshot={"status": "available", "outstanding_amount": 12000, "currency": "INR"},
        promotion_eligible=True,
        credits_registered=18,
        credits_earned=16,
        cgpa=8.2,
    ).insert()


@pytest.mark.anyio
async def test_student_profile_lazy_create(db_ready) -> None:
    _, _, user, scope = await _seed_student(uuid4().hex[:8])
    profile = await get_student_profile(scope, user)
    assert profile.full_name == user.full_name
    stored = await StudentProfile.find_one({"user_id": user.id})
    assert stored is not None


@pytest.mark.anyio
async def test_permitted_profile_update(db_ready) -> None:
    _, _, user, scope = await _seed_student(uuid4().hex[:8])
    updated = await update_student_profile(
        scope,
        user,
        StudentProfileUpdate(contact_phone="+919999999999", bio="Hello"),
    )
    assert updated.contact_phone == "+919999999999"
    assert updated.bio == "Hello"


@pytest.mark.anyio
async def test_profile_update_rejects_extra_fields(db_ready) -> None:
  with pytest.raises(ValidationError):
    StudentProfileUpdate.model_validate({"contact_phone": "+911", "student_id": "HACK"})


@pytest.mark.anyio
async def test_non_student_forbidden(db_ready) -> None:
    tenant = Tenant(name="College", code=f"na_{uuid4().hex[:6]}")
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
        require_student_scope(scope)
    assert exc.value.code == "FORBIDDEN"


@pytest.mark.anyio
async def test_cross_tenant_user_mismatch(db_ready) -> None:
    _, _, _, scope_a = await _seed_student(uuid4().hex[:8])
    tenant_b = Tenant(name="Other", code=f"oth_{uuid4().hex[:6]}")
    await tenant_b.insert()
    other = User(
        email=f"other+{uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Other",
        role=Role.STUDENT,
        tenant_id=tenant_b.id,
    )
    await other.insert()
    with pytest.raises(AppError) as exc:
        await get_student_profile(scope_a, other)
    assert exc.value.code == "FORBIDDEN"


@pytest.mark.anyio
async def test_dashboard_aggregation(db_ready) -> None:
    tenant, _, user, scope = await _seed_student(uuid4().hex[:8])
    await _seed_academic_context(tenant, user)
    dashboard = await get_student_dashboard(scope, user)
    assert dashboard.profile.roll_number == "21CSE001"
    assert len(dashboard.enrolled_courses) == 1
    assert dashboard.enrolled_courses[0].course_code == "CSE101"
    assert dashboard.fees.outstanding_amount == 12000
    stats = await get_dashboard_statistics(scope, user)
    assert stats.enrolled_course_count == 1


@pytest.mark.anyio
async def test_academic_details_and_enrollment_request(db_ready) -> None:
    tenant, _, user, scope = await _seed_student(uuid4().hex[:8])
    await _seed_academic_context(tenant, user)
    details = await get_academic_details(scope, user)
    assert details.admission.programme_code == "BTECH-CSE"
    assert len(details.current_enrollments) == 1
    assert details.academic_record is not None
    assert details.academic_record.cgpa == 8.2

    req = await submit_enrollment_request(
        scope,
        user,
        EnrollmentRequestCreate(
            request_type=StudentAcademicRequestType.SECTION_CHANGE,
            title="Request section B",
            description="Need section change due to lab clash",
            payload={"preferred_section": "B"},
        ),
    )
    assert req.status.value == "submitted"
