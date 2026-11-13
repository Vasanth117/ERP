"""Student phase 6 — exam registration, hall tickets, and results."""

from datetime import datetime, timedelta, timezone
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
from app.modules.academics.models import AcademicYearContext
from app.modules.auth.models import User
from app.modules.examinations.enums import ExaminationEligibilityStatus
from app.modules.examinations.examination_registration_enums import (
    ExaminationFeePaymentStatus,
    HallTicketPublicationStatus,
    SemesterResultPublicationStatus,
)
from app.modules.examinations.examination_registration_models import ExaminationFeePayment, ExaminationRegistrationWindow
from app.modules.examinations.hall_ticket_models import ExaminationHallTicket
from app.modules.examinations.result_publication_models import SemesterResultPublication, SemesterResultSubjectMark
from app.modules.examinations.semester_examination_models import SemesterExaminationSeason, StudentExaminationEligibility
from app.modules.students.examination_registration_enums import ExamRegistrationSubjectType
from app.modules.students.examination_registration_schemas import ExamRegistrationSubmitInput, ExamRegistrationSubjectInput
from app.modules.students.examination_registration_service import (
    download_hall_ticket,
    get_hall_ticket_details,
    submit_examination_registration,
    validate_registration_eligibility,
)
from app.modules.students.examination_results_service import get_published_semester_results, get_subject_wise_marks
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


async def _seed(suffix: str) -> tuple[Tenant, User, AccessScope]:
    tenant = Tenant(name="College", code=f"s6_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await dept.insert()
    user = User(
        email=f"s6+{suffix}@example.com",
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


async def _seed_season(tenant: Tenant, user: User) -> str:
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
    await SemesterExaminationSeason(
        tenant_id=tenant.id,
        season_id=season_id,
        title="End Semester",
        academic_year_label="2025-26",
        semester_label="Odd",
        starts_at=now,
        ends_at=now + timedelta(days=20),
        published=True,
    ).insert()
    await ExaminationRegistrationWindow(
        tenant_id=tenant.id,
        season_id=season_id,
        registration_open_at=now - timedelta(hours=1),
        registration_close_at=now + timedelta(days=5),
        cancellation_deadline=now + timedelta(days=4),
        fee_required=True,
        fee_amount=500,
        fee_code="exam_fee",
    ).insert()
    await StudentExaminationEligibility(
        tenant_id=tenant.id,
        student_user_id=user.id,
        season_id=season_id,
        status=ExaminationEligibilityStatus.ELIGIBLE,
        eligible=True,
        published=True,
        published_at=now,
        semester_course_codes=["CSE101"],
    ).insert()
    await ExaminationFeePayment(
        tenant_id=tenant.id,
        student_user_id=user.id,
        season_id=season_id,
        fee_code="exam_fee",
        amount=500,
        status=ExaminationFeePaymentStatus.PAID,
        verified_at=now,
    ).insert()
    return season_id


@pytest.mark.asyncio
async def test_registration_and_duplicate(db_ready):
    tenant, user, scope = await _seed("a")
    season_id = await _seed_season(tenant, user)
    eligibility = await validate_registration_eligibility(scope, user, season_id)
    assert eligibility.eligible is True
    payload = ExamRegistrationSubmitInput(
        season_id=season_id,
        subjects=[ExamRegistrationSubjectInput(course_code="CSE101", subject_type=ExamRegistrationSubjectType.SEMESTER)],
    )
    reg = await submit_examination_registration(scope, user, payload)
    assert reg.status.value == "submitted"
    with pytest.raises(AppError) as exc:
        await submit_examination_registration(scope, user, payload)
    assert exc.value.code == "DUPLICATE_REGISTRATION"


@pytest.mark.asyncio
async def test_hall_ticket_and_results(db_ready):
    tenant, user, scope = await _seed("b")
    season_id = await _seed_season(tenant, user)
    now = datetime.now(timezone.utc)
    await ExaminationHallTicket(
        tenant_id=tenant.id,
        student_user_id=user.id,
        season_id=season_id,
        ticket_number="HT-1001",
        status=HallTicketPublicationStatus.PUBLISHED,
        document_token="secure-token",
        centre_name="Main Hall",
        published_at=now,
    ).insert()
    details = await get_hall_ticket_details(scope, user, season_id)
    assert details.ticket_number == "HT-1001"
    download = await download_hall_ticket(scope, user, season_id)
    assert download.ticket_number == "HT-1001"
    await SemesterResultPublication(
        tenant_id=tenant.id,
        student_user_id=user.id,
        season_id=season_id,
        academic_year_label="2025-26",
        semester_label="Odd",
        status=SemesterResultPublicationStatus.PUBLISHED,
        overall_pass=True,
        published_at=now,
    ).insert()
    await SemesterResultSubjectMark(
        tenant_id=tenant.id,
        student_user_id=user.id,
        season_id=season_id,
        course_code="CSE101",
        theory_obtained=40,
        theory_max=50,
        total_obtained=75,
        total_max=100,
        pass_fail="pass",
        published=True,
        published_at=now,
    ).insert()
    summary = await get_published_semester_results(scope, user, season_id)
    assert summary.overall_pass is True
    marks = await get_subject_wise_marks(scope, user, season_id=season_id)
    assert marks[0].theory_obtained == 40


@pytest.mark.asyncio
async def test_unpublished_results_hidden(db_ready):
    tenant, user, scope = await _seed("c")
    season_id = await _seed_season(tenant, user)
    await SemesterResultPublication(
        tenant_id=tenant.id,
        student_user_id=user.id,
        season_id=season_id,
        academic_year_label="2025-26",
        semester_label="Odd",
        status=SemesterResultPublicationStatus.PROCESSING,
    ).insert()
    with pytest.raises(AppError) as exc:
        await get_published_semester_results(scope, user, season_id)
    assert exc.value.status_code == 404
