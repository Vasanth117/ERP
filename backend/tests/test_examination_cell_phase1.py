"""Examination cell phase 1 — dashboard and exam session management."""

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
from app.modules.auth.models import User
from app.modules.examinations.enums import ExaminationEligibilityStatus, MarksBatchStatus
from app.modules.examinations.exam_cell_dashboard_service import get_examination_dashboard
from app.modules.examinations.exam_cell_enums import ExamSessionLifecycleAction, ExamSessionStatus, ExamSessionType
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_schemas import ExamSessionAcademicScopeInput, ExamSessionCreate, ExamSessionTransitionRequest
from app.modules.examinations.exam_cell_session_service import create_exam_session, transition_exam_session
from app.modules.examinations.examination_registration_enums import HallTicketPublicationStatus
from app.modules.examinations.hall_ticket_models import ExaminationHallTicket
from app.modules.examinations.models import MarksSubmissionBatch
from app.modules.examinations.semester_examination_models import StudentExaminationEligibility
from app.modules.students.examination_registration_enums import StudentExamRegistrationStatus
from app.modules.students.examination_registration_models import StudentExamRegistration
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


def _scope(user: User, role: Role) -> AccessScope:
    return AccessScope(
        role=role,
        user_id=user.id,
        tenant_id=user.tenant_id,
        department_id=None,
        effective_permissions=permissions_for_role(role),
    )


def _session_payload(suffix: str, *, session_code: str | None = None) -> ExamSessionCreate:
    now = utcnow()
    return ExamSessionCreate(
        session_code=session_code or f"NOV-{suffix}",
        name=f"November Examination {suffix}",
        examination_type=ExamSessionType.REGULAR,
        academic_year_label="2025-26",
        semester_label="Odd",
        season_id=f"season_{suffix}",
        registration_start_at=now,
        registration_end_at=now + timedelta(days=10),
        examination_start_at=now + timedelta(days=15),
        examination_end_at=now + timedelta(days=25),
        result_processing_deadline_at=now + timedelta(days=40),
        academic_scope=ExamSessionAcademicScopeInput(department_codes=[f"CSE{suffix}"]),
    )


async def _seed_tenant(suffix: str) -> tuple[Tenant, User, AccessScope, User]:
    tenant = Tenant(name=f"ExamCell {suffix}", code=f"exam_{suffix}")
    await tenant.insert()
    exam_user = User(
        email=f"examcell+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Examination Officer",
        role=Role.EXAMINATION_CELL,
        tenant_id=tenant.id,
    )
    student = User(
        email=f"student+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    outsider = User(
        email=f"outsider+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Other College",
        role=Role.EXAMINATION_CELL,
        tenant_id=tenant.id,
    )
    await exam_user.insert()
    await student.insert()
    await outsider.insert()
    other_tenant = Tenant(name=f"Other {suffix}", code=f"oth_{suffix}")
    await other_tenant.insert()
    outsider.tenant_id = other_tenant.id
    await outsider.save()
    return tenant, exam_user, _scope(exam_user, Role.EXAMINATION_CELL), outsider


@pytest.mark.asyncio
async def test_examination_cell_permissions(db_ready):
    perms = permissions_for_role(Role.EXAMINATION_CELL)
    assert Permission.EXAMINATION_CELL_DASHBOARD_READ in perms
    assert Permission.EXAMINATION_CELL_SESSION_MANAGE in perms


@pytest.mark.asyncio
async def test_create_exam_session_and_duplicate_code(db_ready):
    suffix = uuid4().hex[:8]
    tenant, exam_user, scope, _ = await _seed_tenant(suffix)
    payload = _session_payload(suffix)
    created = await create_exam_session(scope, exam_user, payload)
    assert created.status == ExamSessionStatus.DRAFT
    assert created.season_id == payload.season_id
    with pytest.raises(AppError) as dup:
        await create_exam_session(scope, exam_user, payload)
    assert dup.value.code == "DUPLICATE_SESSION_CODE"


@pytest.mark.asyncio
async def test_invalid_session_dates(db_ready):
    suffix = uuid4().hex[:8]
    _, exam_user, scope, _ = await _seed_tenant(suffix)
    now = utcnow()
    payload = ExamSessionCreate(
        session_code=f"BAD-{suffix}",
        name="Invalid Dates",
        academic_year_label="2025-26",
        semester_label="Odd",
        registration_start_at=now + timedelta(days=5),
        registration_end_at=now + timedelta(days=2),
        examination_start_at=now + timedelta(days=10),
        examination_end_at=now + timedelta(days=20),
    )
    with pytest.raises(AppError) as exc:
        await create_exam_session(scope, exam_user, payload)
    assert exc.value.code == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_status_transitions(db_ready):
    suffix = uuid4().hex[:8]
    _, exam_user, scope, _ = await _seed_tenant(suffix)
    created = await create_exam_session(scope, exam_user, _session_payload(suffix, session_code=f"TR-{suffix}"))
    session_id = created.id
    from app.common.ids import to_object_id

    oid = to_object_id(session_id, "id")
    moved = await transition_exam_session(
        scope,
        exam_user,
        oid,
        ExamSessionTransitionRequest(action=ExamSessionLifecycleAction.SCHEDULE),
    )
    assert moved.status == ExamSessionStatus.SCHEDULED
    with pytest.raises(AppError) as bad:
        await transition_exam_session(
            scope,
            exam_user,
            oid,
            ExamSessionTransitionRequest(action=ExamSessionLifecycleAction.PUBLISH_RESULTS),
        )
    assert bad.value.code == "INVALID_TRANSITION"


@pytest.mark.asyncio
async def test_dashboard_aggregation_and_tenant_isolation(db_ready):
    suffix = uuid4().hex[:8]
    tenant, exam_user, scope, outsider = await _seed_tenant(suffix)
    season_id = f"season_{suffix}"
    await create_exam_session(scope, exam_user, _session_payload(suffix))

    await StudentExamRegistration(
        tenant_id=tenant.id,
        user_id=exam_user.id,
        season_id=season_id,
        registration_id=f"reg_{suffix}",
        academic_year_label="2025-26",
        semester_label="Odd",
        status=StudentExamRegistrationStatus.CONFIRMED,
    ).insert()
    await StudentExaminationEligibility(
        tenant_id=tenant.id,
        student_user_id=exam_user.id,
        season_id=season_id,
        status=ExaminationEligibilityStatus.PENDING_REVIEW,
    ).insert()
    await ExaminationHallTicket(
        tenant_id=tenant.id,
        student_user_id=exam_user.id,
        season_id=season_id,
        ticket_number=f"HT-{suffix}",
        status=HallTicketPublicationStatus.PUBLISHED,
    ).insert()
    await MarksSubmissionBatch(
        tenant_id=tenant.id,
        faculty_user_id=exam_user.id,
        assessment_id=f"a_{suffix}",
        component_id=f"c_{suffix}",
        course_code="CSE101",
        section="A",
        status=MarksBatchStatus.PENDING_APPROVAL,
    ).insert()

    overview = await get_examination_dashboard(scope, exam_user, academic_year_label="2025-26")
    assert overview.sessions.total >= 1
    assert overview.registration.total_registered_candidates >= 1
    assert overview.registration.pending_eligibility_checks >= 1
    assert overview.hall_tickets.generated >= 1
    assert overview.marks.marks_batches_pending_approval >= 1

    outsider_scope = _scope(outsider, Role.EXAMINATION_CELL)
    other_overview = await get_examination_dashboard(outsider_scope, outsider)
    assert other_overview.sessions.total == 0

    wrong = await ExamSession.find_one({"tenant_id": tenant.id})
    assert wrong is not None
    other_tenant_session = await ExamSession.find_one({"tenant_id": outsider.tenant_id})
    assert other_tenant_session is None