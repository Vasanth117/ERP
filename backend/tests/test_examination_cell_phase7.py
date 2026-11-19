"""Examination cell phase 7 — revaluation, supplementary, incidents."""

from uuid import uuid4

import pytest

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_incident_schemas import (
    ExamDisciplinaryDecisionCreate,
    ExamIncidentAssignInvestigator,
    ExamIncidentCreate,
    ExamInvestigationStatement,
    ExamMalpracticeCaseCreate,
    ExamMalpracticeFinding,
)
from app.modules.examinations.exam_cell_incident_service import (
    assign_investigator,
    get_malpractice_case,
    open_malpractice_case,
    record_disciplinary_decision,
    record_investigation_statement,
    record_malpractice_finding,
    register_incident,
)
from app.modules.examinations.exam_cell_revaluation_enums import ExamDisciplinaryActionType, ExamRevaluationApplicationType
from app.modules.examinations.exam_cell_revaluation_schemas import (
    ExamRevaluationApply,
    ExamRevaluationApprovalDecision,
    ExamRevaluationAssignEvaluator,
    ExamRevaluationRecordEvaluation,
    ExamSupplementaryRegister,
)
from app.modules.examinations.exam_cell_revaluation_service import (
    apply_revaluation,
    assign_revaluation_evaluator,
    decide_revaluation,
    record_revaluation_evaluation,
    register_supplementary,
    supplementary_eligibility,
)
from app.modules.students.arrear_backlog_enums import BacklogStatus
from app.modules.students.arrear_backlog_models import StudentArrearReference
from app.modules.tenants.models import Tenant
from test_examination_cell_phase6 import _seed_published_session


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


@pytest.mark.asyncio
async def test_phase7_permissions(db_ready):
    perms = permissions_for_role(Role.EXAMINATION_CELL)
    assert Permission.EXAMINATION_CELL_REVALUATION_MANAGE in perms
    assert Permission.EXAMINATION_CELL_INCIDENT_INVESTIGATE in perms


@pytest.mark.asyncio
async def test_revaluation_preserves_history_and_recalculates(db_ready):
    suffix = uuid4().hex[:8]
    scope, exam_user, student, session_id, publication_id = await _seed_published_session(suffix)
    faculty = User(
        email=f"eval+p7+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Evaluator",
        role=Role.FACULTY,
        tenant_id=exam_user.tenant_id,
    )
    await faculty.insert()

    app = await apply_revaluation(
        scope,
        exam_user,
        ExamRevaluationApply(
            application_type=ExamRevaluationApplicationType.REVALUATION,
            student_user_id=str(student.id),
            exam_session_id=session_id,
            course_code="CSE101",
            season_id=f"season_{suffix}",
        ),
    )
    await assign_revaluation_evaluator(
        scope,
        exam_user,
        app.application_id,
        ExamRevaluationAssignEvaluator(evaluator_user_id=str(faculty.id)),
    )
    await record_revaluation_evaluation(
        _scope(faculty),
        faculty,
        app.application_id,
        ExamRevaluationRecordEvaluation(revised_marks=90, revised_max_marks=100, findings="Rechecked"),
    )
    updated = await decide_revaluation(
        scope,
        exam_user,
        app.application_id,
        ExamRevaluationApprovalDecision(approved=True, comment="Marks increased"),
    )
    assert updated.status.value == "approved"


@pytest.mark.asyncio
async def test_supplementary_registration(db_ready):
    suffix = uuid4().hex[:8]
    scope, exam_user, student, session_id, _ = await _seed_published_session(suffix)
    await StudentArrearReference(
        tenant_id=exam_user.tenant_id,
        user_id=student.id,
        course_code="CSE101",
        backlog_status=BacklogStatus.PENDING,
    ).insert()
    elig = await supplementary_eligibility(scope, str(student.id))
    assert "CSE101" in elig.eligible_courses
    reg = await register_supplementary(
        scope,
        exam_user,
        ExamSupplementaryRegister(
            student_user_id=str(student.id),
            exam_session_id=session_id,
            course_codes=["CSE101"],
        ),
    )
    assert reg.status.value == "confirmed"


@pytest.mark.asyncio
async def test_malpractice_investigation_workflow(db_ready):
    suffix = uuid4().hex[:8]
    scope, exam_user, student, session_id, publication_id = await _seed_published_session(suffix)

    from app.common.time import utcnow

    incident = await register_incident(
        scope,
        exam_user,
        ExamIncidentCreate(
            exam_session_id=session_id,
            incident_type="malpractice_allegation",
            occurred_at=utcnow(),
            description="Suspected copying during examination",
            student_user_ids=[str(student.id)],
        ),
    )
    case = await open_malpractice_case(
        scope,
        exam_user,
        ExamMalpracticeCaseCreate(
            incident_id=incident.incident_id,
            student_user_id=str(student.id),
            course_code="CSE101",
            allegation_summary="Alleged use of unauthorized material",
        ),
    )
    await assign_investigator(
        scope,
        exam_user,
        case.case_id,
        ExamIncidentAssignInvestigator(investigator_user_id=str(exam_user.id)),
    )
    await record_investigation_statement(
        scope,
        exam_user,
        case.case_id,
        ExamInvestigationStatement(statement="Student denied allegation"),
    )
    closed = await record_malpractice_finding(
        scope,
        exam_user,
        case.case_id,
        ExamMalpracticeFinding(finding_summary="Insufficient evidence", proven=False),
    )
    assert closed.proven is False

    await record_disciplinary_decision(
        scope,
        exam_user,
        case.case_id,
        ExamDisciplinaryDecisionCreate(action_type=ExamDisciplinaryActionType.WARNING, details="Formal warning", result_withheld=False),
    )
    refreshed = await get_malpractice_case(scope, case.case_id)
    assert refreshed.status.value == "closed"


@pytest.mark.asyncio
async def test_unauthorized_malpractice_access(db_ready):
    suffix = uuid4().hex[:8]
    scope, exam_user, student, session_id, _ = await _seed_published_session(suffix)
    outsider = User(
        email=f"outsider+p7+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Outsider",
        role=Role.FACULTY,
        tenant_id=exam_user.tenant_id,
    )
    await outsider.insert()
    from app.common.time import utcnow

    incident = await register_incident(
        scope,
        exam_user,
        ExamIncidentCreate(
            exam_session_id=session_id,
            incident_type="other",
            occurred_at=utcnow(),
            description="Minor disruption",
        ),
    )
    case = await open_malpractice_case(
        scope,
        exam_user,
        ExamMalpracticeCaseCreate(
            incident_id=incident.incident_id,
            student_user_id=str(student.id),
            allegation_summary="Unauthorized material suspected",
        ),
    )
    with pytest.raises(AppError) as exc:
        await get_malpractice_case(_scope(outsider), case.case_id)
    assert exc.value.code == "FORBIDDEN"