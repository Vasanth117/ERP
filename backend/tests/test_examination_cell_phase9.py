"""Examination cell phase 9 — integration, security and audit."""

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
from app.modules.examinations.exam_cell_marks_enums import ExamMarksSubmissionStatus
from app.modules.examinations.exam_cell_marks_service import approve_marks
from app.modules.examinations.exam_cell_redaction import redact_mapping
from app.modules.examinations.exam_cell_security_enums import ExamIntegrationTarget
from app.modules.examinations.exam_cell_security_models import ExamAuditLog, ExamSecurityEvent
from app.modules.examinations.exam_cell_security_schemas import ExamAuditSearch, ExamIntegrationSyncRequest
from app.modules.examinations.exam_cell_security_service import (
    integration_health_report,
    list_integration_configs,
    run_integration_sync,
    search_exam_audit,
)
from app.modules.examinations.exam_cell_audit import record_exam_audit
from app.modules.examinations.exam_cell_incident_service import get_malpractice_case
from test_examination_cell_phase6 import _seed_published_session
from test_examination_cell_phase4 import _seed_phase4


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
async def test_phase9_permissions(db_ready):
    perms = permissions_for_role(Role.EXAMINATION_CELL)
    assert Permission.EXAMINATION_CELL_AUDIT_READ in perms
    assert Permission.EXAMINATION_CELL_INTEGRATION_MANAGE in perms


@pytest.mark.asyncio
async def test_audit_redaction_and_search(db_ready):
    suffix = uuid4().hex[:8]
    scope, exam_user, _, session_id, _ = await _seed_published_session(suffix)
    await record_exam_audit(
        exam_user.tenant_id,
        actor_id=exam_user.id,
        action="exam.test.audit",
        resource_type="exam_session",
        resource_id=session_id,
        before_state={"password": "secret123", "status": "draft"},
        after_state={"status": "open"},
    )
    page = await search_exam_audit(scope, type("P", (), {"offset": 0, "limit": 20})(), ExamAuditSearch(action_prefix="exam.test"))
    assert page.total >= 1
    assert page.items[0].before_state.get("password") == "[REDACTED]"
    assert await ExamAuditLog.find(ExamAuditLog.tenant_id == exam_user.tenant_id).count() >= 1


@pytest.mark.asyncio
async def test_integration_sync_idempotent(db_ready):
    suffix = uuid4().hex[:8]
    scope, exam_user, _, _, _ = await _seed_published_session(suffix)
    await list_integration_configs(scope)
    key = f"sync_{suffix}"
    first = await run_integration_sync(
        scope,
        exam_user,
        ExamIntegrationTarget.STUDENT_MANAGEMENT.value,
        ExamIntegrationSyncRequest(idempotency_key=key),
    )
    second = await run_integration_sync(
        scope,
        exam_user,
        ExamIntegrationTarget.STUDENT_MANAGEMENT.value,
        ExamIntegrationSyncRequest(idempotency_key=key),
    )
    assert first.sync_id == second.sync_id
    report = await integration_health_report(scope)
    assert report.targets_total >= 10


@pytest.mark.asyncio
async def test_marks_approval_separation_of_duties(db_ready):
    suffix = uuid4().hex[:8]
    _tenant, exam_user, faculty, scope, student, session_id, config_id = await _seed_phase4(suffix)
    from app.modules.examinations.exam_cell_marks_schemas import ExamMarksAccessGrant, ExamMarksComponentInput, ExamMarksEntryUpsert, ExamMarksSubmitRequest
    from app.modules.examinations.exam_cell_marks_service import grant_marks_access, submit_marks
    from app.modules.examinations.exam_cell_marks_models import ExamMarksSubmission

    submission = await grant_marks_access(
        scope,
        exam_user,
        ExamMarksAccessGrant(
            exam_session_id=str(session_id),
            course_code="CSE101",
            assessment_config_id=config_id,
            primary_examiner_user_id=str(faculty.id),
        ),
    )
    faculty_scope = _scope(faculty)
    from app.modules.examinations.exam_cell_marks_service import save_marks_draft

    await save_marks_draft(
        faculty_scope,
        faculty,
        submission.submission_id,
        ExamMarksEntryUpsert(
            student_user_id=str(student.id),
            components=[ExamMarksComponentInput(component_code="THEORY", marks_obtained=70, max_marks=100)],
        ),
    )
    await submit_marks(faculty_scope, faculty, submission.submission_id, ExamMarksSubmitRequest())
    sub = await ExamMarksSubmission.find_one(ExamMarksSubmission.submission_id == submission.submission_id)
    assert sub is not None
    sub.primary_examiner_user_id = exam_user.id
    sub.status = ExamMarksSubmissionStatus.SUBMITTED
    await sub.save()
    with pytest.raises(AppError) as exc:
        await approve_marks(scope, exam_user, sub.submission_id)
    assert exc.value.code == "FORBIDDEN"
    events = await ExamSecurityEvent.find(ExamSecurityEvent.tenant_id == exam_user.tenant_id).to_list()
    assert any(e.event_type == "separation_of_duties" for e in events)


@pytest.mark.asyncio
async def test_unauthorized_malpractice_and_audit(db_ready):
    suffix = uuid4().hex[:8]
    scope, exam_user, student, session_id, _ = await _seed_published_session(suffix)
    outsider = User(
        email=f"out+sod+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Outsider",
        role=Role.FACULTY,
        tenant_id=exam_user.tenant_id,
    )
    await outsider.insert()
    from app.common.time import utcnow
    from app.modules.examinations.exam_cell_incident_schemas import ExamIncidentCreate, ExamMalpracticeCaseCreate
    from app.modules.examinations.exam_cell_incident_service import open_malpractice_case, register_incident

    incident = await register_incident(
        scope,
        exam_user,
        ExamIncidentCreate(
            exam_session_id=session_id,
            incident_type="other",
            occurred_at=utcnow(),
            description="Minor issue during exam",
        ),
    )
    case = await open_malpractice_case(
        scope,
        exam_user,
        ExamMalpracticeCaseCreate(
            incident_id=incident.incident_id,
            student_user_id=str(student.id),
            allegation_summary="Suspected unauthorized material",
        ),
    )
    with pytest.raises(AppError):
        await get_malpractice_case(_scope(outsider), case.case_id)


@pytest.mark.asyncio
async def test_redact_mapping():
    payload = redact_mapping({"token": "abc", "course_code": "CSE101"})
    assert payload["token"] == "[REDACTED]"
    assert payload["course_code"] == "CSE101"