"""College Admin phase 4 — faculty/employee and attendance administration."""

from datetime import date
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.attendance.enums import (
    AttendanceCorrectionStatus,
    AttendanceMarkStatus,
    AttendanceSessionStatus,
)
from app.modules.attendance.models import (
    AttendanceCorrectionRequest,
    AttendancePolicyReference,
    AttendanceRecord,
    AttendanceSession,
)
from app.modules.auth.models import User
from app.modules.college_admin.attendance_admin_schemas import (
    AttendancePolicyUpsert,
    CorrectionDecision,
)
from app.modules.college_admin.attendance_admin_service import (
    decide_correction,
    upsert_attendance_policy,
)
from app.modules.college_admin.faculty_admin_schemas import (
    FacultyRecordCreate,
    TeachingAssignmentCreate,
    WorkloadAllocate,
)
from app.modules.college_admin.faculty_admin_service import (
    allocate_workload,
    assign_teaching,
    create_faculty_record,
    get_faculty_record,
)
from app.modules.faculty.models import FacultyAssignment, FacultyProfile
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
    tenant = Tenant(name=f"College P4 {suffix}", code=f"p4_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+p4+{suffix}@example.com",
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
async def test_create_faculty_and_duplicate_employee_id(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, scope = await _seed_admin(suffix)
    dept = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await dept.insert()
    eid = f"EMP-{suffix}"
    created = await create_faculty_record(
        scope,
        FacultyRecordCreate(
            email=f"faculty+{suffix}@example.com",
            password="password1234567890",
            full_name="Dr Faculty",
            employee_id=eid,
            faculty_code=f"FC-{suffix}",
            department_id=str(dept.id),
            designation="Assistant Professor",
        ),
    )
    assert created.employee_id == eid
    profile = await FacultyProfile.find_one(
        Eq(FacultyProfile.tenant_id, tenant.id),
        Eq(FacultyProfile.user_id, to_object_id(created.user_id, "user_id")),
    )
    assert profile is not None
    assert profile.faculty_code == f"FC-{suffix}"

    with pytest.raises(AppError) as dup:
        await create_faculty_record(
            scope,
            FacultyRecordCreate(
                email=f"faculty2+{suffix}@example.com",
                password="password1234567890",
                full_name="Other",
                employee_id=eid,
            ),
        )
    assert dup.value.status_code == 409


@pytest.mark.anyio
async def test_teaching_assignment_and_workload(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, scope = await _seed_admin(suffix)
    dept = Department(tenant_id=tenant.id, name="ECE", code="ECE")
    await dept.insert()
    faculty = await create_faculty_record(
        scope,
        FacultyRecordCreate(
            email=f"teach+{suffix}@example.com",
            password="password1234567890",
            full_name="Teacher",
            department_id=str(dept.id),
        ),
    )
    await assign_teaching(
        scope,
        to_object_id(faculty.record_id, "record_id"),
        TeachingAssignmentCreate(
            academic_year_label="2025",
            semester_label="Sem-1",
            course_code="EC101",
            course_name="Circuits",
            section="A",
        ),
    )
    count = await FacultyAssignment.find(Eq(FacultyAssignment.tenant_id, tenant.id)).count()
    assert count == 1
    await allocate_workload(
        scope,
        to_object_id(faculty.record_id, "record_id"),
        WorkloadAllocate(academic_year_label="2025", semester_label="Sem-1", lecture_hours=12, lab_hours=6),
    )


@pytest.mark.anyio
async def test_attendance_policy_sync_and_correction_approval(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, admin, admin_scope = await _seed_admin(suffix)
    faculty_user = User(
        email=f"fatt+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Faculty Att",
        role=Role.FACULTY,
        tenant_id=tenant.id,
    )
    await faculty_user.insert()
    student_user = User(
        email=f"satt+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student Att",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student_user.insert()

    await upsert_attendance_policy(
        admin_scope,
        AttendancePolicyUpsert(policy_code="default", title="Student policy", submission_deadline_hours=48),
    )
    ref = await AttendancePolicyReference.find_one(Eq(AttendancePolicyReference.tenant_id, tenant.id))
    assert ref is not None
    assert ref.rules.min_percentage_required == 75.0

    session = AttendanceSession(
        tenant_id=tenant.id,
        faculty_user_id=faculty_user.id,
        course_id="c1",
        course_code="CS101",
        section="A",
        session_date=date.today(),
        academic_year_label="2025",
        semester_label="Sem-1",
        status=AttendanceSessionStatus.SUBMITTED,
    )
    await session.insert()
    record = AttendanceRecord(
        tenant_id=tenant.id,
        session_id=session.id,
        student_user_id=student_user.id,
        status=AttendanceMarkStatus.ABSENT,
    )
    await record.insert()
    correction = AttendanceCorrectionRequest(
        tenant_id=tenant.id,
        faculty_user_id=faculty_user.id,
        session_id=session.id,
        student_user_id=student_user.id,
        requested_status=AttendanceMarkStatus.PRESENT,
        reason="Error in class",
        status=AttendanceCorrectionStatus.PENDING,
    )
    await correction.insert()

    result = await decide_correction(
        admin_scope,
        CorrectionDecision(request_id=str(correction.id), decision=AttendanceCorrectionStatus.APPROVED, reviewer_note="OK"),
    )
    assert result["applied_to_record"] is True
    refreshed = await AttendanceRecord.get(record.id)
    assert refreshed is not None
    assert refreshed.status == AttendanceMarkStatus.PRESENT
    session_after = await AttendanceSession.get(session.id)
    assert session_after is not None
    assert session_after.status == AttendanceSessionStatus.SUBMITTED


@pytest.mark.anyio
async def test_faculty_admin_permission_denied(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, _ = await _seed_admin(suffix)
    faculty = User(
        email=f"noperm+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Faculty",
        role=Role.FACULTY,
        tenant_id=tenant.id,
    )
    await faculty.insert()
    scope = AccessScope(
        role=Role.FACULTY,
        user_id=faculty.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.FACULTY),
    )
    with pytest.raises(AppError) as exc:
        await create_faculty_record(
            scope,
            FacultyRecordCreate(email=f"x+{suffix}@example.com", password="password1234567890", full_name="X"),
        )
    assert exc.value.status_code == 403
    assert Permission.FACULTY_ADMIN_MANAGE not in scope.effective_permissions


@pytest.mark.anyio
async def test_tenant_isolation_faculty_record(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, _, scope_a = await _seed_admin(f"a{suffix}")
    _, _, scope_b = await _seed_admin(f"b{suffix}")
    created = await create_faculty_record(
        scope_a,
        FacultyRecordCreate(
            email=f"iso+{suffix}@example.com",
            password="password1234567890",
            full_name="Iso Faculty",
        ),
    )
    with pytest.raises(AppError) as exc:
        await get_faculty_record(scope_b, to_object_id(created.record_id, "record_id"))
    assert exc.value.status_code == 404
