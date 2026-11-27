"""Student phase 3 — timetable and attendance."""

from datetime import date, datetime, time, timedelta, timezone
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.curriculum_models import EnrollmentRosterEntry
from app.modules.academics.models import AcademicYearContext, TimetableEntry
from app.modules.attendance.enums import AttendanceMarkStatus, AttendanceSessionStatus
from app.modules.attendance.models import AttendancePolicyReference, AttendanceRecord, AttendanceSession
from app.modules.auth.models import User
from app.modules.students.attendance_portal_service import (
    get_attendance_summary,
    submit_discrepancy_request,
)
from app.modules.students.student_schedule_schemas import DiscrepancyRequestCreate
from app.modules.students.timetable_service import (
    get_daily_timetable,
    get_timetable_daily_page,
    get_timetable_overview,
    get_timetable_session_detail,
    get_timetable_weekly_page,
    get_weekly_timetable,
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


async def _seed(scope_suffix: str) -> tuple[Tenant, User, AccessScope]:
    tenant = Tenant(name="College", code=f"s3_{scope_suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await dept.insert()
    user = User(
        email=f"s3+{scope_suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        department_id=dept.id,
    )
    await user.insert()
    scope = AccessScope(
        role=Role.STUDENT,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=dept.id,
        effective_permissions=permissions_for_role(Role.STUDENT),
    )
    return tenant, user, scope


async def _seed_timetable_attendance(tenant: Tenant, user: User) -> None:
    await AcademicYearContext(
        tenant_id=tenant.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        is_current=True,
    ).insert()
    await EnrollmentRosterEntry(
        tenant_id=tenant.id,
        course_id="c101",
        course_code="CSE101",
        section_code="A",
        student_user_id=user.id,
        roll_number="R001",
        display_name="Student",
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
    await AttendancePolicyReference(tenant_id=tenant.id, policy_code="default").insert()
    session = AttendanceSession(
        tenant_id=tenant.id,
        faculty_user_id=user.id,
        course_id="c101",
        course_code="CSE101",
        section="A",
        session_date=date.today(),
        academic_year_label="2025-26",
        semester_label="Odd",
        status=AttendanceSessionStatus.SUBMITTED,
        submitted_at=datetime.now(timezone.utc),
    )
    await session.insert()
    await AttendanceRecord(
        tenant_id=tenant.id,
        session_id=session.id,
        student_user_id=user.id,
        status=AttendanceMarkStatus.PRESENT,
    ).insert()


@pytest.mark.anyio
async def test_daily_and_weekly_timetable(db_ready) -> None:
    tenant, user, scope = await _seed(uuid4().hex[:8])
    await _seed_timetable_attendance(tenant, user)
    # Timetable seed uses day_of_week=0 (Monday)
    anchor = date.today()
    while anchor.weekday() != 0:
        anchor -= timedelta(days=1)
    daily = await get_daily_timetable(scope, user, anchor_date=anchor)
    assert any(s.course_code == "CSE101" for s in daily.slots)
    weekly = await get_weekly_timetable(scope, user)
    assert len(weekly.days) == 7


@pytest.mark.anyio
async def test_timetable_overview(db_ready) -> None:
    tenant, user, scope = await _seed(uuid4().hex[:8])
    await _seed_timetable_attendance(tenant, user)
    anchor = date.today()
    while anchor.weekday() != 0:
        anchor -= timedelta(days=1)
    overview = await get_timetable_overview(scope, user, anchor_date=anchor)
    assert overview.kpis.classes_today >= 1
    assert overview.kpis.classes_this_week >= 1
    assert len(overview.today_rows) >= 1
    assert overview.today_rows[0].subject_label == "Programming"


@pytest.mark.anyio
async def test_timetable_daily_and_weekly_page_dtos(db_ready) -> None:
    tenant, user, scope = await _seed(uuid4().hex[:8])
    await _seed_timetable_attendance(tenant, user)
    anchor = date.today()
    while anchor.weekday() != 0:
        anchor -= timedelta(days=1)
    daily_page = await get_timetable_daily_page(scope, user, anchor_date=anchor)
    assert daily_page.page_title == "Daily timetable"
    assert len(daily_page.timeline_rows) >= 1
    assert daily_page.session_detail is not None
    weekly_page = await get_timetable_weekly_page(scope, user, anchor_date=anchor)
    assert weekly_page.page_title == "Weekly timetable"
    assert len(weekly_page.days) == 7


@pytest.mark.anyio
async def test_timetable_session_detail_from_database(db_ready) -> None:
    tenant, user, scope = await _seed(uuid4().hex[:8])
    await _seed_timetable_attendance(tenant, user)
    anchor = date.today()
    while anchor.weekday() != 0:
        anchor -= timedelta(days=1)
    daily_page = await get_timetable_daily_page(scope, user, anchor_date=anchor)
    assert daily_page.timeline_rows
    slot_id = daily_page.timeline_rows[0].slot_id
    detail = await get_timetable_session_detail(scope, user, slot_id, anchor_date=anchor)
    assert detail.slot_id == slot_id
    assert any(f.label == "Course" and f.value == "CSE101" for f in detail.fields)


@pytest.mark.anyio
async def test_attendance_summary_and_discrepancy(db_ready) -> None:
    tenant, user, scope = await _seed(uuid4().hex[:8])
    await _seed_timetable_attendance(tenant, user)
    summary = await get_attendance_summary(scope, user)
    assert summary.subjects[0].course_code == "CSE101"
    assert summary.subjects[0].percentage == 100.0
    session = await AttendanceSession.find_one({"tenant_id": tenant.id})
    assert session is not None
    req = await submit_discrepancy_request(
        scope,
        user,
        DiscrepancyRequestCreate(session_id=str(session.id), claimed_status=AttendanceMarkStatus.PRESENT, reason="I was present in class today"),
    )
    assert req.status.value == "pending"


@pytest.mark.anyio
async def test_cross_tenant_discrepancy_blocked(db_ready) -> None:
    tenant_a, user_a, scope_a = await _seed(uuid4().hex[:8])
    _, user_b, scope_b = await _seed(uuid4().hex[:8])
    await _seed_timetable_attendance(tenant_a, user_a)
    session = await AttendanceSession.find_one({"tenant_id": tenant_a.id})
    assert session is not None
    with pytest.raises(AppError) as exc:
        await submit_discrepancy_request(
            scope_b,
            user_b,
            DiscrepancyRequestCreate(
                session_id=str(session.id),
                claimed_status=AttendanceMarkStatus.PRESENT,
                reason="Attempt cross-tenant discrepancy request",
            ),
        )
    assert exc.value.code in {"NOT_FOUND", "FORBIDDEN", "TENANT_REQUIRED"}
