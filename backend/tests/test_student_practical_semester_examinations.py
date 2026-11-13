"""Student phase 5 — practical/model exams and semester examinations."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.curriculum_models import EnrollmentRosterEntry
from app.modules.academics.enums import SessionType
from app.modules.academics.models import AcademicYearContext, ExaminationSchedule, TimetableEntry
from app.modules.auth.models import User
from app.modules.examinations.enums import AssessmentComponentType, ExaminationEligibilityStatus, StudentMarkStatus
from app.modules.examinations.models import Assessment, AssessmentComponent, StudentAssessmentMark
from app.modules.examinations.semester_examination_models import (
    ExaminationCentre,
    SemesterExaminationSeason,
    SemesterExaminationSession,
    StudentExaminationEligibility,
)
from app.modules.students.practical_examination_service import (
    get_published_practical_marks,
    get_practical_schedules,
    get_unpublished_practical_marks,
)
from app.modules.students.semester_examination_service import (
    get_examination_centres,
    get_examination_eligibility,
    get_semester_examination_schedules,
)
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


async def _seed(suffix: str) -> tuple[Tenant, User, User, AccessScope, AccessScope]:
    tenant = Tenant(name="College", code=f"s5_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await dept.insert()
    student = User(
        email=f"s5+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        department_id=dept.id,
    )
    other = User(
        email=f"s5other+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Other",
        role=Role.STUDENT,
        tenant_id=tenant.id,
        department_id=dept.id,
    )
    await student.insert()
    await other.insert()
    scope = AccessScope(
        role=Role.STUDENT,
        user_id=student.id,
        tenant_id=tenant.id,
        department_id=dept.id,
        effective_permissions=permissions_for_role(Role.STUDENT),
    )
    other_scope = AccessScope(
        role=Role.STUDENT,
        user_id=other.id,
        tenant_id=tenant.id,
        department_id=dept.id,
        effective_permissions=permissions_for_role(Role.STUDENT),
    )
    return tenant, student, other, scope, other_scope


async def _seed_practical(tenant: Tenant, student: User) -> None:
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
        student_user_id=student.id,
        roll_number="R100",
        display_name="Student",
        academic_year_label="2025-26",
        semester_label="Odd",
    ).insert()
    await TimetableEntry(
        tenant_id=tenant.id,
        faculty_user_id=student.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        day_of_week=1,
        start_time=datetime.now(timezone.utc).time(),
        end_time=(datetime.now(timezone.utc) + timedelta(hours=2)).time(),
        course_code="CSE101",
        course_name="Programming Lab",
        section="A",
        session_type=SessionType.LABORATORY,
        laboratory="Lab-1",
    ).insert()
    await ExaminationSchedule(
        tenant_id=tenant.id,
        course_code="CSE101",
        section="A",
        exam_type="practical",
        title="Practical Exam",
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=3),
        academic_year_label="2025-26",
        semester_label="Odd",
        room="Lab-1",
    ).insert()
    await Assessment(
        tenant_id=tenant.id,
        assessment_id="asm-practical",
        course_id="c101",
        course_code="CSE101",
        title="Practical bundle",
        academic_year_label="2025-26",
        semester_label="Odd",
    ).insert()
    await AssessmentComponent(
        tenant_id=tenant.id,
        assessment_id="asm-practical",
        component_id="cmp1",
        code="PR1",
        name="Record",
        component_type=AssessmentComponentType.PRACTICAL,
        max_marks=50,
        weight_percent=50,
    ).insert()
    await StudentAssessmentMark(
        tenant_id=tenant.id,
        batch_id=student.id,
        assessment_id="asm-practical",
        component_id="cmp1",
        student_user_id=student.id,
        marks_obtained=42,
        max_marks=50,
        status=StudentMarkStatus.APPROVED,
    ).insert()


async def _seed_semester(tenant: Tenant, student: User) -> str:
    season_id = f"season-{uuid4().hex[:8]}"
    await SemesterExaminationSeason(
        tenant_id=tenant.id,
        season_id=season_id,
        title="End Semester 2025",
        academic_year_label="2025-26",
        semester_label="Odd",
        starts_at=datetime.now(timezone.utc),
        ends_at=datetime.now(timezone.utc) + timedelta(days=14),
        published=True,
    ).insert()
    await SemesterExaminationSession(
        tenant_id=tenant.id,
        season_id=season_id,
        session_code="SES1",
        course_code="CSE101",
        course_name="Programming",
        section="A",
        scheduled_start=datetime.now(timezone.utc) + timedelta(days=5),
        centre_code="MAIN",
        room="Hall-A",
        instructions="Bring hall ticket",
        published=True,
    ).insert()
    await ExaminationCentre(
        tenant_id=tenant.id,
        centre_code="MAIN",
        name="Main Campus",
        building="Block A",
        address="City",
    ).insert()
    await StudentExaminationEligibility(
        tenant_id=tenant.id,
        student_user_id=student.id,
        season_id=season_id,
        status=ExaminationEligibilityStatus.ELIGIBLE,
        eligible=True,
        published=True,
        published_at=datetime.now(timezone.utc),
    ).insert()
    return season_id


@pytest.mark.asyncio
async def test_practical_schedules_and_marks(db_ready):
    tenant, student, _, scope, _ = await _seed("a")
    await _seed_practical(tenant, student)
    schedules = await get_practical_schedules(scope, student)
    assert len(schedules) >= 1
    published = await get_published_practical_marks(scope, student)
    assert len(published) == 1
    assert published[0].marks_obtained == 42
    unpublished = await get_unpublished_practical_marks(scope, student)
    assert unpublished == []


@pytest.mark.asyncio
async def test_unpublished_practical_placeholder(db_ready):
    tenant, student, _, scope, _ = await _seed("b")
    await _seed_practical(tenant, student)
    await StudentAssessmentMark.find_one(
        {
            "tenant_id": tenant.id,
            "student_user_id": student.id,
            "status": StudentMarkStatus.APPROVED,
        }
    ).set({StudentAssessmentMark.status: StudentMarkStatus.DRAFT})
    rows = await get_unpublished_practical_marks(scope, student)
    assert len(rows) == 1
    assert rows[0].visibility == "unpublished"


@pytest.mark.asyncio
async def test_semester_schedules_and_eligibility(db_ready):
    tenant, student, _, scope, _ = await _seed("c")
    await _seed_practical(tenant, student)
    season_id = await _seed_semester(tenant, student)
    sessions = await get_semester_examination_schedules(scope, student)
    assert len(sessions) == 1
    assert sessions[0].session_code == "SES1"
    centres = await get_examination_centres(scope, student)
    assert centres[0].centre_code == "MAIN"
    eligibility = await get_examination_eligibility(scope, student, season_id=season_id)
    assert eligibility.eligible is True


@pytest.mark.asyncio
async def test_cross_student_isolation(db_ready):
    tenant, student, other, _, other_scope = await _seed("d")
    await _seed_practical(tenant, student)
    await _seed_semester(tenant, student)
    other_sessions = await get_semester_examination_schedules(other_scope, other)
    assert other_sessions == []
