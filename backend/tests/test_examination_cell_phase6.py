"""Examination cell phase 6 — publication and academic documents."""

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
from app.modules.examinations.exam_cell_document_service import download_document, generate_document, verify_document
from app.modules.examinations.exam_cell_eligibility_service import evaluate_student_eligibility
from app.modules.examinations.exam_cell_enums import ExamSessionLifecycleAction, ExamSessionType
from app.modules.examinations.exam_cell_grading_schemas import (
    ExamGradeBoundaryInput,
    ExamGradingPolicyActivate,
    ExamGradingPolicyCreate,
    ExamProvisionalCalculateRequest,
)
from app.modules.examinations.exam_cell_grading_service import activate_grading_policy, calculate_provisional_results, create_grading_policy
from app.modules.examinations.exam_cell_marks_schemas import ExamMarksAccessGrant, ExamMarksComponentInput, ExamMarksEntryUpsert, ExamMarksSubmitRequest
from app.modules.examinations.exam_cell_marks_service import approve_marks, grant_marks_access, save_marks_draft, submit_marks
from app.modules.examinations.exam_cell_publication_enums import ExamResultDocumentType
from app.modules.examinations.exam_cell_publication_schemas import (
    ExamDocumentGenerateRequest,
    ExamDocumentVerifyRequest,
    ExamPublicationApprove,
    ExamPublicationCreate,
    ExamPublicationProcessRequest,
    ExamPublicationWithholdRequest,
)
from app.modules.examinations.exam_cell_publication_schemas import ExamPublicationProcessRequest
from app.modules.examinations.exam_cell_publication_service import (
    approve_publication,
    create_publication,
    list_student_published_results,
    publish_results,
    validate_publication_ready,
    withhold_student_result,
)
from app.modules.examinations.exam_cell_registration_schemas import ExamEligibilityEvaluateRequest, ExamRegistrationCreate, ExamRegistrationSubjectInput
from app.modules.examinations.exam_cell_registration_service import register_student
from app.modules.examinations.exam_cell_result_schemas import ExamResultReviewComment, ExamResultReviewDecision, ExamResultReviewStart
from app.modules.examinations.exam_cell_result_service import approve_results, department_review_comment, exam_cell_verify, start_result_review
from app.modules.examinations.exam_cell_schemas import ExamSessionAcademicScopeInput, ExamSessionCreate, ExamSessionTransitionRequest
from app.modules.examinations.exam_cell_session_service import create_exam_session, transition_exam_session
from app.modules.examinations.examination_registration_enums import ExaminationFeePaymentStatus
from app.modules.examinations.examination_registration_models import ExaminationFeePayment
from app.modules.students.curriculum_models import CourseCatalogReference
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


async def _seed_published_session(suffix: str):
    tenant = Tenant(name=f"ExamP6 {suffix}", code=f"exp6_{suffix}")
    await tenant.insert()
    exam_user = User(
        email=f"examcell+p6+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Examination Officer",
        role=Role.EXAMINATION_CELL,
        tenant_id=tenant.id,
    )
    student = User(
        email=f"student+p6+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student One",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    faculty_examiner = User(
        email=f"faculty+p6+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Primary Examiner",
        role=Role.FACULTY,
        tenant_id=tenant.id,
    )
    marks_moderator = User(
        email=f"moderator+p6+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Marks Moderator",
        role=Role.EXAMINATION_CELL,
        tenant_id=tenant.id,
    )
    await exam_user.insert()
    await student.insert()
    await faculty_examiner.insert()
    await marks_moderator.insert()
    scope = _scope(exam_user)

    await StudentProfile(tenant_id=tenant.id, user_id=student.id, roll_number=f"ROLL{suffix}", programme_code="BTECH").insert()
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
    await CourseCatalogReference(
        tenant_id=tenant.id,
        programme_code="BTECH",
        academic_year_label="2025-26",
        semester_label="Odd",
        course_id=f"c_{suffix}",
        course_code="CSE101",
        credit_units=3,
    ).insert()

    now = utcnow()
    session = await create_exam_session(
        scope,
        exam_user,
        ExamSessionCreate(
            session_code=f"P6-{suffix}",
            name="Phase 6 Session",
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

    submission = await grant_marks_access(
        scope,
        exam_user,
        ExamMarksAccessGrant(
            exam_session_id=session.id,
            course_code="CSE101",
            assessment_config_id=config.config_id,
            primary_examiner_user_id=str(faculty_examiner.id),
        ),
    )
    await save_marks_draft(
        scope,
        exam_user,
        submission.submission_id,
        ExamMarksEntryUpsert(
            student_user_id=str(student.id),
            components=[ExamMarksComponentInput(component_code="THEORY", marks_obtained=88, max_marks=100)],
        ),
    )
    await submit_marks(scope, exam_user, submission.submission_id, ExamMarksSubmitRequest())
    moderator_scope = _scope(marks_moderator)
    await approve_marks(moderator_scope, marks_moderator, submission.submission_id)

    policy = await create_grading_policy(
        scope,
        exam_user,
        ExamGradingPolicyCreate(
            policy_code=f"REG-{suffix}",
            title="Reg",
            programme_code="BTECH",
            academic_year_label="2025-26",
            boundaries=[
                ExamGradeBoundaryInput(min_percent=80, max_percent=100, grade_letter="A", grade_point=9, is_passing=True),
                ExamGradeBoundaryInput(min_percent=0, max_percent=79.99, grade_letter="F", grade_point=0, is_passing=False, sort_order=2),
            ],
        ),
    )
    await activate_grading_policy(scope, exam_user, policy.policy_id, ExamGradingPolicyActivate())
    await calculate_provisional_results(
        scope,
        exam_user,
        ExamProvisionalCalculateRequest(exam_session_id=session.id, programme_code="BTECH"),
    )

    workflow = await start_result_review(scope, exam_user, ExamResultReviewStart(exam_session_id=session.id))
    await department_review_comment(scope, exam_user, workflow.workflow_id, ExamResultReviewComment(comment="OK"))
    await exam_cell_verify(scope, exam_user, workflow.workflow_id)
    await approve_results(scope, exam_user, workflow.workflow_id, ExamResultReviewDecision(approve=True))

    pub = await create_publication(
        scope,
        exam_user,
        ExamPublicationCreate(exam_session_id=session.id, workflow_id=workflow.workflow_id),
    )
    await approve_publication(scope, exam_user, pub.publication_id, ExamPublicationApprove())
    published = await publish_results(moderator_scope, marks_moderator, pub.publication_id)

    return scope, exam_user, student, session.id, published.publication_id


@pytest.mark.asyncio
async def test_phase6_permissions(db_ready):
    perms = permissions_for_role(Role.EXAMINATION_CELL)
    assert Permission.EXAMINATION_CELL_PUBLICATION_PUBLISH in perms
    assert Permission.EXAMINATION_CELL_DOCUMENT_GENERATE in perms


@pytest.mark.asyncio
async def test_publication_and_student_visibility(db_ready):
    suffix = uuid4().hex[:8]
    scope, exam_user, student, session_id, publication_id = await _seed_published_session(suffix)
    student_scope = _scope(student)

    rows = await list_student_published_results(student_scope, str(student.id))
    assert len(rows) == 1
    assert rows[0].grade_letter == "A"

    await withhold_student_result(
        scope,
        exam_user,
        publication_id,
        ExamPublicationWithholdRequest(student_user_id=str(student.id), withhold=True),
    )
    assert await list_student_published_results(student_scope, str(student.id)) == []


@pytest.mark.asyncio
async def test_document_generation_and_verify(db_ready):
    suffix = uuid4().hex[:8]
    scope, exam_user, student, _, publication_id = await _seed_published_session(suffix)

    doc = await generate_document(
        scope,
        exam_user,
        ExamDocumentGenerateRequest(
            publication_id=publication_id,
            student_user_id=str(student.id),
            document_type=ExamResultDocumentType.GRADE_CARD,
        ),
    )
    pdf, name = await download_document(scope, exam_user, doc.document_id)
    assert pdf.startswith(b"%PDF")
    assert name.endswith(".pdf")

    ok = await verify_document(scope, ExamDocumentVerifyRequest(document_id=doc.document_id, verification_code=doc.verification_code))
    assert ok.valid is True

    bad = await verify_document(scope, ExamDocumentVerifyRequest(document_id=doc.document_id, verification_code="INVALID"))
    assert bad.valid is False


@pytest.mark.asyncio
async def test_unpublished_document_blocked(db_ready):
    suffix = uuid4().hex[:8]
    scope, exam_user, student, session_id, _ = await _seed_published_session(suffix)
    report = await validate_publication_ready(scope, ExamPublicationProcessRequest(exam_session_id=session_id))
    assert report.ready is True
    draft = await create_publication(scope, exam_user, ExamPublicationCreate(exam_session_id=session_id))
    with pytest.raises(AppError) as exc:
        await generate_document(
            scope,
            exam_user,
            ExamDocumentGenerateRequest(
                publication_id=draft.publication_id,
                student_user_id=str(student.id),
                document_type=ExamResultDocumentType.MARKSHEET,
            ),
        )
    assert exc.value.code == "FORBIDDEN"