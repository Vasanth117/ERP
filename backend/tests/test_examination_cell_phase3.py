"""Examination cell phase 3 — eligibility, registration, hall tickets."""

from datetime import timedelta
from uuid import uuid4

import pytest

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.time import utcnow
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.curriculum_models import EnrollmentRosterEntry
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_eligibility_service import evaluate_student_eligibility
from app.modules.examinations.exam_cell_enums import ExamSessionLifecycleAction, ExamSessionStatus, ExamSessionType
from app.modules.examinations.exam_cell_hall_ticket_schemas import ExamHallTicketGenerateRequest, ExamHallTicketVerifyRequest
from app.modules.examinations.exam_cell_hall_ticket_service import generate_hall_ticket, publish_hall_ticket, verify_hall_ticket
from app.modules.examinations.exam_cell_registration_schemas import (
    ExamBulkRegistrationCreate,
    ExamEligibilityEvaluateRequest,
    ExamRegistrationCreate,
    ExamRegistrationSubjectInput,
)
from app.modules.examinations.exam_cell_registration_enums import ExamRegistrationSubjectType
from app.modules.examinations.exam_cell_registration_service import bulk_register_students, register_student
from app.modules.examinations.exam_cell_schemas import ExamSessionAcademicScopeInput, ExamSessionCreate, ExamSessionTransitionRequest
from app.modules.examinations.exam_cell_session_service import create_exam_session, transition_exam_session
from app.modules.examinations.exam_cell_timetable_enums import ExamTimetableStatus
from app.modules.examinations.exam_cell_timetable_models import ExamTimetable, ExamTimetableEntry
from app.modules.examinations.examination_registration_enums import ExaminationFeePaymentStatus
from app.modules.examinations.examination_registration_models import ExaminationFeePayment
from app.modules.students.enums import StudentEnrollmentStatus
from app.modules.students.models import StudentAcademicRecord, StudentProfile
from app.modules.tenants.models import Tenant


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


def _scope(user: User) -> AccessScope:
    return AccessScope(
        role=user.role,
        user_id=user.id,
        tenant_id=user.tenant_id,
        department_id=None,
        effective_permissions=permissions_for_role(user.role),
    )


async def _seed_phase3(suffix: str) -> tuple[Tenant, User, AccessScope, User, str]:
    tenant = Tenant(name=f"ExamP3 {suffix}", code=f"exp3_{suffix}")
    await tenant.insert()
    exam_user = User(
        email=f"examcell+p3+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Examination Officer",
        role=Role.EXAMINATION_CELL,
        tenant_id=tenant.id,
    )
    student = User(
        email=f"student+p3+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student One",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    outsider = User(
        email=f"outsider+p3+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Other College",
        role=Role.EXAMINATION_CELL,
        tenant_id=tenant.id,
    )
    await exam_user.insert()
    await student.insert()
    await outsider.insert()
    other = Tenant(name=f"OtherP3 {suffix}", code=f"othp3_{suffix}")
    await other.insert()
    outsider.tenant_id = other.id
    await outsider.save()
    scope = _scope(exam_user)

    await StudentProfile(
        tenant_id=tenant.id,
        user_id=student.id,
        roll_number=f"ROLL{suffix}",
        programme_code="BTECH",
    ).insert()
    await StudentAcademicRecord(
        tenant_id=tenant.id,
        user_id=student.id,
        academic_year_label="2025-26",
        semester_label="Odd",
        enrollment_status=StudentEnrollmentStatus.ACTIVE,
    ).insert()
    await EnrollmentRosterEntry(
        tenant_id=tenant.id,
        student_user_id=student.id,
        course_id=f"c_{suffix}",
        academic_year_label="2025-26",
        semester_label="Odd",
        course_code="CSE101",
        section_code="A",
        roll_number=f"ROLL{suffix}",
        display_name="Student One",
    ).insert()

    now = utcnow()
    session = await create_exam_session(
        scope,
        exam_user,
        ExamSessionCreate(
            session_code=f"P3-{suffix}",
            name="Phase 3 Session",
            examination_type=ExamSessionType.REGULAR,
            academic_year_label="2025-26",
            semester_label="Odd",
            season_id=f"season_{suffix}",
            registration_start_at=now - timedelta(days=1),
            registration_end_at=now + timedelta(days=10),
            examination_start_at=now + timedelta(days=15),
            examination_end_at=now + timedelta(days=25),
            academic_scope=ExamSessionAcademicScopeInput(department_codes=["CSE"]),
        ),
    )
    from app.common.ids import to_object_id

    session_oid = to_object_id(session.id, "id")
    for action in (
        ExamSessionLifecycleAction.SCHEDULE,
        ExamSessionLifecycleAction.OPEN_REGISTRATION,
    ):
        await transition_exam_session(scope, exam_user, session_oid, ExamSessionTransitionRequest(action=action))

    await ExaminationFeePayment(
        tenant_id=tenant.id,
        student_user_id=student.id,
        season_id=f"season_{suffix}",
        fee_code="exam_fee",
        amount=500,
        status=ExaminationFeePaymentStatus.PAID,
    ).insert()

    tt = ExamTimetable(
        tenant_id=tenant.id,
        timetable_id=f"ett_{suffix}",
        exam_session_id=session_oid,
        title="Exam TT",
        status=ExamTimetableStatus.PUBLISHED,
        published_version=1,
        published_at=now,
    )
    await tt.insert()
    await ExamTimetableEntry(
        tenant_id=tenant.id,
        timetable_id=tt.id,
        entry_code=f"ENT-{suffix}",
        course_code="CSE101",
        student_group_label="BTECH:2023:A:CSE101",
        scheduled_start=now + timedelta(days=16),
        scheduled_end=now + timedelta(days=16, hours=3),
        duration_minutes=180,
        centre_code="MAIN",
        room_label="HALL-A",
    ).insert()

    return tenant, exam_user, scope, student, session.id


@pytest.mark.asyncio
async def test_phase3_permissions(db_ready):
    perms = permissions_for_role(Role.EXAMINATION_CELL)
    assert Permission.EXAMINATION_CELL_REGISTRATION_MANAGE in perms
    assert Permission.EXAMINATION_CELL_HALL_TICKET_PUBLISH in perms


@pytest.mark.asyncio
async def test_eligibility_and_registration_flow(db_ready):
    suffix = uuid4().hex[:8]
    _, exam_user, scope, student, session_id = await _seed_phase3(suffix)
    eligibility = await evaluate_student_eligibility(
        scope,
        exam_user,
        ExamEligibilityEvaluateRequest(student_user_id=str(student.id), exam_session_id=session_id, publish=True),
    )
    assert eligibility.overall_eligible is True

    reg = await register_student(
        scope,
        exam_user,
        ExamRegistrationCreate(
            exam_session_id=session_id,
            student_user_id=str(student.id),
            subjects=[
                ExamRegistrationSubjectInput(course_code="CSE101", subject_type=ExamRegistrationSubjectType.SEMESTER)
            ],
            confirm=True,
        ),
    )
    assert reg.status.value == "confirmed"

    with pytest.raises(AppError) as dup:
        await register_student(
            scope,
            exam_user,
            ExamRegistrationCreate(
                exam_session_id=session_id,
                student_user_id=str(student.id),
                subjects=[ExamRegistrationSubjectInput(course_code="CSE101")],
            ),
        )
    assert dup.value.code == "DUPLICATE_REGISTRATION"


@pytest.mark.asyncio
async def test_hall_ticket_generation_and_verification(db_ready):
    suffix = uuid4().hex[:8]
    _, exam_user, scope, student, session_id = await _seed_phase3(suffix)
    await evaluate_student_eligibility(
        scope,
        exam_user,
        ExamEligibilityEvaluateRequest(student_user_id=str(student.id), exam_session_id=session_id, publish=True),
    )
    await register_student(
        scope,
        exam_user,
        ExamRegistrationCreate(
            exam_session_id=session_id,
            student_user_id=str(student.id),
            subjects=[ExamRegistrationSubjectInput(course_code="CSE101")],
            confirm=True,
        ),
    )
    ticket = await generate_hall_ticket(
        scope,
        exam_user,
        ExamHallTicketGenerateRequest(exam_session_id=session_id, student_user_id=str(student.id)),
    )
    published = await publish_hall_ticket(scope, exam_user, ticket.hall_ticket_id)
    assert published.status.value == "published"
    verify_ok = await verify_hall_ticket(
        scope,
        ExamHallTicketVerifyRequest(ticket_number=ticket.ticket_number, verification_code=ticket.verification_code),
    )
    assert verify_ok.valid is True


@pytest.mark.asyncio
async def test_hall_ticket_blocked_without_registration(db_ready):
    suffix = uuid4().hex[:8]
    _, exam_user, scope, student, session_id = await _seed_phase3(suffix)
    await evaluate_student_eligibility(
        scope,
        exam_user,
        ExamEligibilityEvaluateRequest(student_user_id=str(student.id), exam_session_id=session_id, publish=True),
    )
    with pytest.raises(AppError) as exc:
        await generate_hall_ticket(
            scope,
            exam_user,
            ExamHallTicketGenerateRequest(exam_session_id=session_id, student_user_id=str(student.id)),
        )
    assert exc.value.code == "NOT_REGISTERED"


@pytest.mark.asyncio
async def test_cross_tenant_isolation(db_ready):
    suffix = uuid4().hex[:8]
    tenant, exam_user, scope, student, session_id = await _seed_phase3(suffix)
    outsider = await User.find_one({"email": f"outsider+p3+{suffix}@example.com"})
    assert outsider is not None
    outsider_scope = _scope(outsider)
    with pytest.raises(AppError):
        await evaluate_student_eligibility(
            outsider_scope,
            outsider,
            ExamEligibilityEvaluateRequest(student_user_id=str(student.id), exam_session_id=session_id),
        )
    _ = tenant