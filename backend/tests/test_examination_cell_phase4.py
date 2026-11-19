"""Examination cell phase 4 — seating logistics and marks entry."""

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
from app.modules.examinations.exam_cell_assessment_enums import ExamAssessmentComponentKind, ExamAssessmentConfigStatus
from app.modules.examinations.exam_cell_assessment_models import ExamAssessmentComponent, ExamAssessmentConfig
from app.modules.examinations.exam_cell_eligibility_service import evaluate_student_eligibility
from app.modules.examinations.exam_cell_enums import ExamSessionLifecycleAction, ExamSessionType
from app.modules.examinations.exam_cell_marks_enums import ExamMarksSubmissionStatus
from app.modules.examinations.exam_cell_marks_schemas import (
    ExamMarksAccessGrant,
    ExamMarksComponentInput,
    ExamMarksCorrectionRequest,
    ExamMarksEntryUpsert,
    ExamMarksImportRequest,
    ExamMarksImportRow,
    ExamMarksSubmitRequest,
)
from app.modules.examinations.exam_cell_marks_service import (
    apply_marks_correction,
    approve_marks,
    grant_marks_access,
    import_marks,
    request_marks_correction,
    save_marks_draft,
    submit_marks,
)
from app.modules.examinations.exam_cell_registration_schemas import (
    ExamEligibilityEvaluateRequest,
    ExamRegistrationCreate,
    ExamRegistrationSubjectInput,
)
from app.modules.examinations.exam_cell_registration_service import register_student
from app.modules.examinations.exam_cell_schemas import ExamSessionAcademicScopeInput, ExamSessionCreate, ExamSessionTransitionRequest
from app.modules.examinations.exam_cell_seating_schemas import (
    ExamInvigilatorAssignRequest,
    ExamRoomCreate,
    ExamSeatingAllocateRequest,
    ExamSeatingPlanCreate,
    ExamVenueCreate,
)
from app.modules.examinations.exam_cell_seating_service import (
    allocate_seating,
    assign_invigilator,
    create_exam_room,
    create_exam_venue,
    create_seating_plan,
    publish_seating_plan,
)
from app.modules.examinations.exam_cell_session_service import create_exam_session, transition_exam_session
from app.modules.examinations.examination_registration_enums import ExaminationFeePaymentStatus
from app.modules.examinations.examination_registration_models import ExaminationFeePayment
from app.modules.examinations.semester_examination_models import ExaminationCentre
from app.modules.students.enums import StudentEnrollmentStatus
from app.modules.students.models import StudentAcademicRecord, StudentProfile
from app.modules.tenants.models import Tenant
from app.common.ids import to_object_id


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


async def _seed_phase4(suffix: str):
    tenant = Tenant(name=f"ExamP4 {suffix}", code=f"exp4_{suffix}")
    await tenant.insert()
    exam_user = User(
        email=f"examcell+p4+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Examination Officer",
        role=Role.EXAMINATION_CELL,
        tenant_id=tenant.id,
    )
    faculty = User(
        email=f"faculty+p4+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Examiner",
        role=Role.FACULTY,
        tenant_id=tenant.id,
    )
    student = User(
        email=f"student+p4+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student One",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await exam_user.insert()
    await faculty.insert()
    await student.insert()
    scope = _scope(exam_user)

    await ExaminationCentre(
        tenant_id=tenant.id,
        centre_code="MAIN",
        name="Main Block",
        room_labels=["HALL-A"],
        is_active=True,
    ).insert()

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
            session_code=f"P4-{suffix}",
            name="Phase 4 Session",
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
    session_oid = to_object_id(session.id, "id")
    for action in (ExamSessionLifecycleAction.SCHEDULE, ExamSessionLifecycleAction.OPEN_REGISTRATION):
        await transition_exam_session(scope, exam_user, session_oid, ExamSessionTransitionRequest(action=action))

    await ExaminationFeePayment(
        tenant_id=tenant.id,
        student_user_id=student.id,
        season_id=f"season_{suffix}",
        fee_code="exam_fee",
        amount=500,
        status=ExaminationFeePaymentStatus.PAID,
    ).insert()

    await evaluate_student_eligibility(
        scope,
        exam_user,
        ExamEligibilityEvaluateRequest(student_user_id=str(student.id), exam_session_id=session.id, publish=True),
    )
    await register_student(
        scope,
        exam_user,
        ExamRegistrationCreate(
            exam_session_id=session.id,
            student_user_id=str(student.id),
            subjects=[ExamRegistrationSubjectInput(course_code="CSE101")],
            confirm=True,
        ),
    )

    config = ExamAssessmentConfig(
        tenant_id=tenant.id,
        config_id=f"cfg_{suffix}",
        config_code=f"CFG-{suffix}",
        title="CSE101 Assessment",
        semester_label="Odd",
        academic_year_label="2025-26",
        course_code="CSE101",
        status=ExamAssessmentConfigStatus.ACTIVE,
    )
    await config.insert()
    await ExamAssessmentComponent(
        tenant_id=tenant.id,
        config_id=config.config_id,
        component_id=f"cmp_{suffix}",
        code="THEORY",
        name="Theory",
        assessment_type=ExamAssessmentComponentKind.THEORY,
        max_marks=100,
        weight_percent=100,
        passing_marks=40,
    ).insert()

    return tenant, exam_user, faculty, scope, student, session.id, config.config_id


@pytest.mark.asyncio
async def test_phase4_permissions(db_ready):
    perms = permissions_for_role(Role.EXAMINATION_CELL)
    assert Permission.EXAMINATION_CELL_SEATING_PUBLISH in perms
    assert Permission.EXAMINATION_CELL_MARKS_MODERATE in perms


@pytest.mark.asyncio
async def test_seating_allocation_and_publish(db_ready):
    suffix = uuid4().hex[:8]
    _, exam_user, faculty, scope, student, session_id, _ = await _seed_phase4(suffix)

    venue = await create_exam_venue(
        scope,
        exam_user,
        ExamVenueCreate(exam_session_id=session_id, name="Main Hall", centre_code="MAIN"),
    )
    room = await create_exam_room(
        scope,
        exam_user,
        ExamRoomCreate(
            venue_id=venue.venue_id,
            room_label="HALL-A",
            total_capacity=40,
            usable_seating_capacity=30,
        ),
    )
    plan = await create_seating_plan(
        scope,
        exam_user,
        ExamSeatingPlanCreate(exam_session_id=session_id, title="Main seating", course_code="CSE101"),
    )
    allocations = await allocate_seating(
        scope,
        exam_user,
        ExamSeatingAllocateRequest(plan_id=plan.plan_id, course_code="CSE101"),
    )
    assert len(allocations) == 1
    assert allocations[0].seat_number == 1
    assert allocations[0].student_user_id == str(student.id)

    await assign_invigilator(
        scope,
        exam_user,
        ExamInvigilatorAssignRequest(plan_id=plan.plan_id, room_id=room.room_id, faculty_user_id=str(faculty.id)),
    )
    with pytest.raises(AppError) as dup_invigilator:
        await assign_invigilator(
            scope,
            exam_user,
            ExamInvigilatorAssignRequest(plan_id=plan.plan_id, room_id=room.room_id, faculty_user_id=str(faculty.id)),
        )
    assert dup_invigilator.value.code == "CONFLICT"
    published = await publish_seating_plan(scope, exam_user, plan.plan_id)
    assert published.status.value == "published"


@pytest.mark.asyncio
async def test_seating_capacity_guard(db_ready):
    suffix = uuid4().hex[:8]
    _, exam_user, _, scope, _, session_id, _ = await _seed_phase4(suffix)
    venue = await create_exam_venue(
        scope,
        exam_user,
        ExamVenueCreate(exam_session_id=session_id, name="Small Hall", centre_code="MAIN"),
    )
    await create_exam_room(
        scope,
        exam_user,
        ExamRoomCreate(venue_id=venue.venue_id, room_label="HALL-A", total_capacity=0, usable_seating_capacity=0),
    )
    plan = await create_seating_plan(
        scope,
        exam_user,
        ExamSeatingPlanCreate(exam_session_id=session_id, title="Tight plan"),
    )
    with pytest.raises(AppError) as exc:
        await allocate_seating(scope, exam_user, ExamSeatingAllocateRequest(plan_id=plan.plan_id))
    assert exc.value.code == "CAPACITY_EXCEEDED"


@pytest.mark.asyncio
async def test_marks_entry_submit_and_lock(db_ready):
    suffix = uuid4().hex[:8]
    _, exam_user, faculty, scope, student, session_id, config_id = await _seed_phase4(suffix)

    submission = await grant_marks_access(
        scope,
        exam_user,
        ExamMarksAccessGrant(
            exam_session_id=session_id,
            course_code="CSE101",
            assessment_config_id=config_id,
            primary_examiner_user_id=str(faculty.id),
        ),
    )
    faculty_scope = _scope(faculty)
    entry = await save_marks_draft(
        faculty_scope,
        faculty,
        submission.submission_id,
        ExamMarksEntryUpsert(
            student_user_id=str(student.id),
            components=[ExamMarksComponentInput(component_code="THEORY", marks_obtained=72, max_marks=100)],
        ),
    )
    assert entry.total_marks == 72

    with pytest.raises(AppError) as over:
        await save_marks_draft(
            faculty_scope,
            faculty,
            submission.submission_id,
            ExamMarksEntryUpsert(
                student_user_id=str(student.id),
                components=[ExamMarksComponentInput(component_code="THEORY", marks_obtained=150, max_marks=100)],
            ),
        )
    assert over.value.code == "VALIDATION_ERROR"

    submitted = await submit_marks(
        faculty_scope,
        faculty,
        submission.submission_id,
        ExamMarksSubmitRequest(note="Ready"),
    )
    assert submitted.status == ExamMarksSubmissionStatus.SUBMITTED

    approved = await approve_marks(scope, exam_user, submission.submission_id)
    assert approved.status == ExamMarksSubmissionStatus.APPROVED

    with pytest.raises(AppError) as locked:
        await save_marks_draft(
            faculty_scope,
            faculty,
            submission.submission_id,
            ExamMarksEntryUpsert(
                student_user_id=str(student.id),
                components=[ExamMarksComponentInput(component_code="THEORY", marks_obtained=80, max_marks=100)],
            ),
        )
    assert locked.value.code == "MARKS_LOCKED"


@pytest.mark.asyncio
async def test_marks_import_and_correction(db_ready):
    suffix = uuid4().hex[:8]
    _, exam_user, faculty, scope, student, session_id, config_id = await _seed_phase4(suffix)
    submission = await grant_marks_access(
        scope,
        exam_user,
        ExamMarksAccessGrant(
            exam_session_id=session_id,
            course_code="CSE101",
            assessment_config_id=config_id,
            primary_examiner_user_id=str(exam_user.id),
        ),
    )
    faculty_scope = _scope(exam_user)
    draft = await save_marks_draft(
        faculty_scope,
        exam_user,
        submission.submission_id,
        ExamMarksEntryUpsert(
            student_user_id=str(student.id),
            components=[ExamMarksComponentInput(component_code="THEORY", marks_obtained=60, max_marks=100)],
        ),
    )
    result = await import_marks(
        faculty_scope,
        exam_user,
        submission.submission_id,
        ExamMarksImportRequest(
            rows=[
                ExamMarksImportRow(
                    roll_number=f"ROLL{suffix}",
                    component_code="THEORY",
                    marks_obtained=65,
                    max_marks=100,
                )
            ]
        ),
    )
    assert result.accepted == 1
    assert result.rejected == 0

    await submit_marks(faculty_scope, exam_user, submission.submission_id, ExamMarksSubmitRequest())
    correction = await request_marks_correction(
        faculty_scope,
        exam_user,
        submission.submission_id,
        ExamMarksCorrectionRequest(entry_id=draft.entry_id, component_code="THEORY", requested_marks=68, reason="Tabulation"),
    )
    resolved = await apply_marks_correction(scope, exam_user, correction.correction_id, approve=True)
    assert resolved.status.value == "approved"


@pytest.mark.asyncio
async def test_unauthorized_marks_entry(db_ready):
    suffix = uuid4().hex[:8]
    _, exam_user, faculty, scope, student, session_id, config_id = await _seed_phase4(suffix)
    outsider = User(
        email=f"outsider+p4+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Outsider Faculty",
        role=Role.FACULTY,
        tenant_id=exam_user.tenant_id,
    )
    await outsider.insert()
    submission = await grant_marks_access(
        scope,
        exam_user,
        ExamMarksAccessGrant(
            exam_session_id=session_id,
            course_code="CSE101",
            assessment_config_id=config_id,
            primary_examiner_user_id=str(faculty.id),
        ),
    )
    with pytest.raises(AppError) as exc:
        await save_marks_draft(
            _scope(outsider),
            outsider,
            submission.submission_id,
            ExamMarksEntryUpsert(
                student_user_id=str(student.id),
                components=[ExamMarksComponentInput(component_code="THEORY", marks_obtained=50, max_marks=100)],
            ),
        )
    assert exc.value.code == "FORBIDDEN"