"""Faculty phase 4 — assessment and student support."""

from uuid import uuid4

import pytest
from beanie import PydanticObjectId

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.academics.curriculum_models import CourseRecord, EnrollmentRosterEntry
from app.modules.examinations.approval import approve_marks_batch
from app.modules.examinations.enums import AssessmentComponentType
from app.modules.examinations.models import (
    Assessment,
    AssessmentComponent,
    FacultyAssessmentAssignment,
)
from app.modules.faculty.assessment_schemas import (
    MarkEntryItem,
    MarksCorrectionCreate,
    MarksDraftSave,
    MarksSubmitRequest,
)
from app.modules.faculty.assessment_service import (
    list_assigned_assessments,
    save_marks_draft,
    submit_marks,
    submit_marks_correction,
)
from app.modules.faculty.enums import AssignmentRole, AssignmentStatus
from app.modules.faculty.models import FacultyAssignment
from app.modules.faculty.student_support_service import create_mentoring_record, student_performance_list
from app.modules.faculty.support_schemas import MentoringRecordCreate
from app.modules.auth.models import User
from app.modules.tenants.models import Department, Tenant
from app.modules.examinations.enums import MarksBatchStatus
from app.modules.examinations.models import MarksSubmissionBatch


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


async def _seed_phase4() -> tuple[AccessScope, User, str, PydanticObjectId, str]:
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"C4 {suffix}", code=f"c4_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="CSE", code="CSE")
    await dept.insert()
    faculty = User(
        email=f"f4+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Faculty 4",
        role=Role.FACULTY,
        tenant_id=tenant.id,
        department_id=dept.id,
    )
    await faculty.insert()
    student = User(
        email=f"s4+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    course = CourseRecord(
        tenant_id=tenant.id,
        course_id=f"cid4-{suffix}",
        course_code="CS401",
        name="AI",
        credit_units=3,
    )
    await course.insert()
    await FacultyAssignment(
        tenant_id=tenant.id,
        user_id=faculty.id,
        course_id=course.course_id,
        course_code="CS401",
        course_name="AI",
        section="A",
        academic_year_label="2025-26",
        semester_label="Odd",
        assignment_role=AssignmentRole.PRIMARY,
        status=AssignmentStatus.ACTIVE,
    ).insert()
    await EnrollmentRosterEntry(
        tenant_id=tenant.id,
        course_id=course.course_id,
        course_code="CS401",
        section_code="A",
        student_user_id=student.id,
        roll_number="23CS401",
        display_name="Student",
        academic_year_label="2025-26",
        semester_label="Odd",
    ).insert()
    assessment_id = f"asm-{suffix}"
    await Assessment(
        tenant_id=tenant.id,
        assessment_id=assessment_id,
        course_id=course.course_id,
        course_code="CS401",
        title="CIA",
        academic_year_label="2025-26",
        semester_label="Odd",
    ).insert()
    await AssessmentComponent(
        tenant_id=tenant.id,
        assessment_id=assessment_id,
        component_id="int1",
        code="INT1",
        name="Internal 1",
        component_type=AssessmentComponentType.INTERNAL,
        max_marks=25,
        faculty_may_enter=True,
    ).insert()
    await AssessmentComponent(
        tenant_id=tenant.id,
        assessment_id=assessment_id,
        component_id="final",
        code="FINAL",
        name="Final Exam",
        component_type=AssessmentComponentType.FINAL_EXAM,
        max_marks=75,
        faculty_may_enter=False,
        is_official_final=True,
    ).insert()
    await FacultyAssessmentAssignment(
        tenant_id=tenant.id,
        faculty_user_id=faculty.id,
        assessment_id=assessment_id,
        course_id=course.course_id,
        course_code="CS401",
        section="A",
        academic_year_label="2025-26",
        semester_label="Odd",
    ).insert()
    scope = AccessScope(
        role=Role.FACULTY,
        user_id=faculty.id,
        tenant_id=tenant.id,
        department_id=dept.id,
        effective_permissions=permissions_for_role(Role.FACULTY),
    )
    return scope, faculty, assessment_id, student.id, suffix


def test_grading_letter_from_policy() -> None:
    from app.modules.examinations.grading import letter_grade

    class FakePolicy:
        grade_bands = [{"min": 75, "grade": "A"}]
        pass_percentage = 40.0

    policy = FakePolicy()
    assert letter_grade(80, policy) == "A"
    assert letter_grade(30, policy) == "FAIL"


@pytest.mark.anyio
async def test_assessment_retrieval(db_ready) -> None:
    scope, user, assessment_id, _, _ = await _seed_phase4()
    rows = await list_assigned_assessments(scope, user)
    assert len(rows) == 1
    assert rows[0].assessment_id == assessment_id


@pytest.mark.anyio
async def test_marks_entry_validation(db_ready) -> None:
    scope, user, assessment_id, student_id, _ = await _seed_phase4()
    with pytest.raises(AppError) as exc:
        await save_marks_draft(
            scope,
            user,
            MarksDraftSave(
                assessment_id=assessment_id,
                component_id="int1",
                course_code="CS401",
                section="A",
                entries=[MarkEntryItem(student_user_id=str(student_id), marks_obtained=30)],
            ),
        )
    assert exc.value.code == "VALIDATION_ERROR"


@pytest.mark.anyio
async def test_marks_workflow_and_duplicate(db_ready) -> None:
    scope, user, assessment_id, student_id, _ = await _seed_phase4()
    batch = await save_marks_draft(
        scope,
        user,
        MarksDraftSave(
            assessment_id=assessment_id,
            component_id="int1",
            course_code="CS401",
            section="A",
            entries=[MarkEntryItem(student_user_id=str(student_id), marks_obtained=20)],
        ),
    )
    submitted = await submit_marks(scope, user, MarksSubmitRequest(batch_id=batch.id))
    assert submitted.status in {MarksBatchStatus.PENDING_APPROVAL, MarksBatchStatus.SUBMITTED}
    with pytest.raises(AppError) as exc:
        await save_marks_draft(
            scope,
            user,
            MarksDraftSave(
                assessment_id=assessment_id,
                component_id="int1",
                course_code="CS401",
                section="A",
                entries=[MarkEntryItem(student_user_id=str(student_id), marks_obtained=15)],
            ),
        )
    assert exc.value.code == "CONFLICT"


@pytest.mark.anyio
async def test_final_component_blocked(db_ready) -> None:
    scope, user, assessment_id, student_id, _ = await _seed_phase4()
    with pytest.raises(AppError) as exc:
        await save_marks_draft(
            scope,
            user,
            MarksDraftSave(
                assessment_id=assessment_id,
                component_id="final",
                course_code="CS401",
                section="A",
                entries=[MarkEntryItem(student_user_id=str(student_id), marks_obtained=50)],
            ),
        )
    assert exc.value.code == "FORBIDDEN"


@pytest.mark.anyio
async def test_correction_on_approved_batch(db_ready) -> None:
    scope, user, assessment_id, student_id, _ = await _seed_phase4()
    batch = await save_marks_draft(
        scope,
        user,
        MarksDraftSave(
            assessment_id=assessment_id,
            component_id="int1",
            course_code="CS401",
            section="A",
            entries=[MarkEntryItem(student_user_id=str(student_id), marks_obtained=18)],
        ),
    )
    await submit_marks(scope, user, MarksSubmitRequest(batch_id=batch.id))
    stored = await MarksSubmissionBatch.get(PydanticObjectId(batch.id))
    assert stored is not None
    await approve_marks_batch(scope.tenant_id, stored.id, actor_id=user.id)
    correction = await submit_marks_correction(
        scope,
        user,
        MarksCorrectionCreate(
            batch_id=batch.id,
            student_user_id=str(student_id),
            requested_marks=19.0,
            reason="Data entry typo correction needed",
        ),
    )
    assert correction.status == "pending"


@pytest.mark.anyio
async def test_mentoring_scope(db_ready) -> None:
    scope, user, _, student_id, _ = await _seed_phase4()
    rec = await create_mentoring_record(
        scope,
        user,
        MentoringRecordCreate(student_user_id=str(student_id), course_code="CS401", notes="Weekly check-in"),
    )
    assert rec.notes == "Weekly check-in"


@pytest.mark.anyio
async def test_unauthorized_mentoring_student(db_ready) -> None:
    scope, user, _, _, _ = await _seed_phase4()
    other = PydanticObjectId()
    with pytest.raises(AppError) as exc:
        await create_mentoring_record(
            scope,
            user,
            MentoringRecordCreate(student_user_id=str(other), course_code="CS401", notes="Not allowed"),
        )
    assert exc.value.code == "FORBIDDEN"


@pytest.mark.anyio
async def test_student_performance_aggregation(db_ready) -> None:
    scope, user, _, _, _ = await _seed_phase4()
    rows = await student_performance_list(scope, user)
    assert len(rows) >= 1
