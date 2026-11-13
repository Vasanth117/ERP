"""Student phase 7 — grades, GPA, and academic documents."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.curriculum_models import CourseRecord, EnrollmentRosterEntry
from app.modules.academics.models import AcademicYearContext
from app.modules.auth.models import User
from app.modules.examinations.academic_document_models import AcademicDocumentPublication, AcademicDocumentStatus, AcademicDocumentType
from app.modules.examinations.examination_registration_enums import SemesterResultPublicationStatus
from app.modules.examinations.result_publication_models import SemesterResultPublication, SemesterResultSubjectMark
from app.modules.students.academic_document_service import download_academic_document, get_transcript, list_grade_cards
from app.modules.students.academic_grading_service import get_cgpa, get_semester_gpa, get_subject_grades
from app.modules.students.enums import AcademicStanding
from app.modules.students.models import StudentAcademicRecord
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


async def _seed(suffix: str) -> tuple[Tenant, User, AccessScope, str]:
    tenant = Tenant(name="College", code=f"s7_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await dept.insert()
    user = User(
        email=f"s7+{suffix}@example.com",
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
    season_id = f"season-{uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)
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
        roll_number="R100",
        display_name="Student",
        academic_year_label="2025-26",
        semester_label="Odd",
    ).insert()
    await CourseRecord(
        tenant_id=tenant.id,
        course_id="c101",
        course_code="CSE101",
        name="Programming",
        credit_units=4,
    ).insert()
    await StudentAcademicRecord(
        tenant_id=tenant.id,
        user_id=user.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        academic_standing=AcademicStanding.GOOD,
        credits_earned=4,
        credits_registered=4,
        cgpa=8.5,
    ).insert()
    await SemesterResultPublication(
        tenant_id=tenant.id,
        student_user_id=user.id,
        season_id=season_id,
        academic_year_label="2025-26",
        semester_label="Odd",
        status=SemesterResultPublicationStatus.PUBLISHED,
        overall_pass=True,
        gpa=8.25,
        published_at=now,
    ).insert()
    await SemesterResultSubjectMark(
        tenant_id=tenant.id,
        student_user_id=user.id,
        season_id=season_id,
        course_code="CSE101",
        course_name="Programming",
        grade_letter="A",
        grade_points=9.0,
        credit_units=4,
        total_obtained=80,
        total_max=100,
        pass_fail="pass",
        published=True,
        published_at=now,
    ).insert()
    await AcademicDocumentPublication(
        tenant_id=tenant.id,
        student_user_id=user.id,
        document_id="doc-gc-1",
        document_type=AcademicDocumentType.GRADE_CARD,
        season_id=season_id,
        academic_year_label="2025-26",
        semester_label="Odd",
        title="Grade Card Odd 2025",
        status=AcademicDocumentStatus.PUBLISHED,
        storage_token="token-gc",
        gpa=8.25,
        cgpa=8.5,
        published_at=now,
    ).insert()
    return tenant, user, scope, season_id


@pytest.mark.asyncio
async def test_gpa_and_grades(db_ready):
    tenant, user, scope, season_id = await _seed("a")
    grades = await get_subject_grades(scope, user, season_id=season_id)
    assert grades[0].grade_letter == "A"
    semester = await get_semester_gpa(scope, user, season_id)
    assert semester.gpa == 9.0
    cumulative = await get_cgpa(scope, user)
    assert cumulative.cgpa is not None


@pytest.mark.asyncio
async def test_grade_cards_and_download(db_ready):
    tenant, user, scope, season_id = await _seed("b")
    cards = await list_grade_cards(scope, user, season_id=season_id)
    assert cards[0].document_id == "doc-gc-1"
    download = await download_academic_document(scope, user, "doc-gc-1")
    assert download.download_token


@pytest.mark.asyncio
async def test_unauthorized_document(db_ready):
    tenant, user, scope, _ = await _seed("c")
    with pytest.raises(AppError) as exc:
        await download_academic_document(scope, user, "missing-doc")
    assert exc.value.status_code in {403, 404}
