"""Examination cell — exam registration workflows."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq
from pymongo.errors import DuplicateKeyError

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_audit import record_exam_activity
from app.modules.examinations.exam_cell_enums import ExamSessionStatus
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_policy import (
    authorize_examination_cell_registration_manage,
    require_examination_cell_tenant,
)
from app.modules.examinations.exam_cell_registration_enums import (
    ExamRegistrationHistoryAction,
    ExamRegistrationStatus,
)
from app.modules.examinations.exam_cell_registration_models import (
    ExamEligibilityRecord,
    ExamRegistration,
    ExamRegistrationHistory,
    ExamRegistrationSubject,
)
from app.modules.examinations.exam_cell_registration_schemas import (
    ExamBulkRegistrationCreate,
    ExamRegistrationCorrection,
    ExamRegistrationCreate,
    ExamRegistrationHistoryRead,
    ExamRegistrationRead,
    ExamRegistrationSubjectRead,
    ExamRegistrationSummaryRead,
)
from app.modules.students.policy import require_student_scope


def _registration_id() -> str:
    return f"exr_{uuid4().hex[:10]}"


async def _session(tenant_id: PydanticObjectId, session_oid: PydanticObjectId) -> ExamSession:
    row = await ExamSession.find_one(Eq(ExamSession.tenant_id, tenant_id), Eq(ExamSession.id, session_oid))
    if row is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)
    return row


def _registration_window_open(session: ExamSession) -> bool:
    now = utcnow()
    if session.status != ExamSessionStatus.REGISTRATION_OPEN:
        return False
    start = as_utc_aware(session.registration_start_at)
    end = as_utc_aware(session.registration_end_at)
    return start <= now <= end


async def _write_history(
    tenant_id: PydanticObjectId,
    *,
    registration_id: str,
    exam_session_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    action: ExamRegistrationHistoryAction,
    actor_id: PydanticObjectId | None,
    note: str | None = None,
) -> None:
    await ExamRegistrationHistory(
        tenant_id=tenant_id,
        registration_id=registration_id,
        exam_session_id=exam_session_id,
        student_user_id=student_user_id,
        action=action,
        actor_id=actor_id,
        note=note,
    ).insert()


async def _assert_eligible(tenant_id: PydanticObjectId, student_id: PydanticObjectId, session_id: PydanticObjectId) -> ExamEligibilityRecord:
    row = await ExamEligibilityRecord.find_one(
        Eq(ExamEligibilityRecord.tenant_id, tenant_id),
        Eq(ExamEligibilityRecord.student_user_id, student_id),
        Eq(ExamEligibilityRecord.exam_session_id, session_id),
    )
    if row is None or not row.overall_eligible:
        raise AppError(code="REGISTRATION_NOT_ELIGIBLE", message="Student is not eligible for this session", status_code=403)
    return row


async def _read_registration(tenant_id: PydanticObjectId, registration_id: str) -> ExamRegistrationRead:
    reg = await ExamRegistration.find_one(Eq(ExamRegistration.tenant_id, tenant_id), Eq(ExamRegistration.registration_id, registration_id))
    if reg is None:
        raise AppError(code="NOT_FOUND", message="Registration not found", status_code=404)
    subjects = await ExamRegistrationSubject.find(
        Eq(ExamRegistrationSubject.tenant_id, tenant_id),
        Eq(ExamRegistrationSubject.registration_id, registration_id),
    ).to_list()
    return ExamRegistrationRead(
        registration_id=reg.registration_id,
        exam_session_id=str(reg.exam_session_id),
        season_id=reg.season_id,
        student_user_id=str(reg.student_user_id),
        status=reg.status,
        fee_verified=reg.fee_verified,
        subjects=[
            ExamRegistrationSubjectRead(
                course_code=s.course_code,
                subject_code=s.subject_code,
                paper_code=s.paper_code,
                subject_type=s.subject_type,
            )
            for s in subjects
        ],
        submitted_at=reg.submitted_at,
        confirmed_at=reg.confirmed_at,
        cancelled_at=reg.cancelled_at,
        created_at=reg.created_at,
    )


async def _create_registration(
    scope: AccessScope,
    actor: User,
    *,
    tenant_id: PydanticObjectId,
    session: ExamSession,
    student_id: PydanticObjectId,
    payload: ExamRegistrationCreate | ExamBulkRegistrationCreate,
    bulk: bool,
) -> ExamRegistrationRead:
    if not _registration_window_open(session):
        raise AppError(code="REGISTRATION_CLOSED", message="Registration window is closed", status_code=403)
    eligibility = await _assert_eligible(tenant_id, student_id, session.id)
    active = await ExamRegistration.find_one(
        {
            "tenant_id": tenant_id,
            "student_user_id": student_id,
            "exam_session_id": session.id,
            "status": {
                "$nin": [
                    ExamRegistrationStatus.CANCELLED.value,
                    ExamRegistrationStatus.REJECTED.value,
                ]
            },
        }
    )
    if active:
        raise AppError(code="DUPLICATE_REGISTRATION", message="Active registration already exists", status_code=409)

    registration_id = _registration_id()
    status = ExamRegistrationStatus.CONFIRMED if payload.confirm else ExamRegistrationStatus.SUBMITTED
    reg = ExamRegistration(
        tenant_id=tenant_id,
        registration_id=registration_id,
        exam_session_id=session.id,
        season_id=session.season_id,
        student_user_id=student_id,
        academic_year_label=session.academic_year_label,
        semester_label=session.semester_label,
        status=status,
        fee_verified=eligibility.overall_eligible,
        submitted_at=utcnow(),
        confirmed_at=utcnow() if payload.confirm else None,
        created_by=actor.id,
    )
    await reg.insert()
    try:
        for subject in payload.subjects:
            await ExamRegistrationSubject(
                tenant_id=tenant_id,
                registration_id=registration_id,
                student_user_id=student_id,
                exam_session_id=session.id,
                course_code=subject.course_code,
                subject_code=subject.subject_code,
                paper_code=subject.paper_code,
                subject_type=subject.subject_type,
            ).insert()
    except DuplicateKeyError as exc:
        await reg.delete()
        raise AppError(code="DUPLICATE_REGISTRATION", message="Duplicate subject registration", status_code=409) from exc

    action = ExamRegistrationHistoryAction.BULK_REGISTERED if bulk else ExamRegistrationHistoryAction.SUBMITTED
    if payload.confirm:
        action = ExamRegistrationHistoryAction.CONFIRMED
    await _write_history(
        tenant_id,
        registration_id=registration_id,
        exam_session_id=session.id,
        student_user_id=student_id,
        action=action,
        actor_id=actor.id,
    )
    await record_exam_activity(
        tenant_id,
        actor_id=actor.id,
        action="exam_registration.created",
        summary=f"Registration {registration_id} for session {session.session_code}",
        exam_session_id=session.id,
        season_id=session.season_id,
        metadata={"registration_id": registration_id, "student_user_id": str(student_id)},
    )
    if payload.confirm:
        from app.modules.examinations.exam_cell_notification_triggers import notify_registration_confirmed

        subjects = await ExamRegistrationSubject.find(
            Eq(ExamRegistrationSubject.tenant_id, tenant_id),
            Eq(ExamRegistrationSubject.registration_id, registration_id),
        ).to_list()
        await notify_registration_confirmed(
            tenant_id,
            student_user_id=student_id,
            exam_session_id=session.id,
            session_name=session.name or session.session_code,
            registration_id=registration_id,
            subject_count=len(subjects),
        )
    return await _read_registration(tenant_id, registration_id)


async def register_student(
    scope: AccessScope,
    actor: User,
    payload: ExamRegistrationCreate,
) -> ExamRegistrationRead:
    if payload.student_user_id:
        authorize_examination_cell_registration_manage(scope)
        tenant_id = require_examination_cell_tenant(scope)
        student_id = to_object_id(payload.student_user_id, "student_user_id")
    else:
        authorize(scope, Permission.STUDENT_EXAM_REGISTRATION_MANAGE)
        tenant_id = require_student_scope(scope)
        student_id = actor.id
    session_id = to_object_id(payload.exam_session_id, "exam_session_id")
    session = await _session(tenant_id, session_id)
    return await _create_registration(scope, actor, tenant_id=tenant_id, session=session, student_id=student_id, payload=payload, bulk=False)


async def bulk_register_students(scope: AccessScope, actor: User, payload: ExamBulkRegistrationCreate) -> list[ExamRegistrationRead]:
    authorize_examination_cell_registration_manage(scope)
    tenant_id = require_examination_cell_tenant(scope)
    session_id = to_object_id(payload.exam_session_id, "exam_session_id")
    session = await _session(tenant_id, session_id)
    results: list[ExamRegistrationRead] = []
    for sid in payload.student_user_ids:
        student_id = to_object_id(sid, "student_user_id")
        single = ExamRegistrationCreate(
            exam_session_id=payload.exam_session_id,
            student_user_id=sid,
            subjects=payload.subjects,
            confirm=payload.confirm,
        )
        results.append(await _create_registration(scope, actor, tenant_id=tenant_id, session=session, student_id=student_id, payload=single, bulk=True))
    return results


async def cancel_registration(scope: AccessScope, actor: User, registration_id: str) -> ExamRegistrationRead:
    tenant_id = require_examination_cell_tenant(scope)
    reg = await ExamRegistration.find_one(Eq(ExamRegistration.tenant_id, tenant_id), Eq(ExamRegistration.registration_id, registration_id))
    if reg is None:
        raise AppError(code="NOT_FOUND", message="Registration not found", status_code=404)
    if actor.id != reg.student_user_id:
        authorize_examination_cell_registration_manage(scope)
    if reg.status == ExamRegistrationStatus.CANCELLED:
        raise AppError(code="ALREADY_CANCELLED", message="Registration already cancelled", status_code=409)
    reg.status = ExamRegistrationStatus.CANCELLED
    reg.cancelled_at = utcnow()
    reg.updated_at = utcnow()
    await reg.save()
    await ExamRegistrationSubject.find(
        Eq(ExamRegistrationSubject.tenant_id, tenant_id),
        Eq(ExamRegistrationSubject.registration_id, registration_id),
    ).delete()
    await _write_history(
        tenant_id,
        registration_id=registration_id,
        exam_session_id=reg.exam_session_id,
        student_user_id=reg.student_user_id,
        action=ExamRegistrationHistoryAction.CANCELLED,
        actor_id=actor.id,
    )
    return await _read_registration(tenant_id, registration_id)


async def correct_registration(
    scope: AccessScope,
    actor: User,
    registration_id: str,
    payload: ExamRegistrationCorrection,
) -> ExamRegistrationRead:
    authorize_examination_cell_registration_manage(scope)
    tenant_id = require_examination_cell_tenant(scope)
    reg = await ExamRegistration.find_one(Eq(ExamRegistration.tenant_id, tenant_id), Eq(ExamRegistration.registration_id, registration_id))
    if reg is None:
        raise AppError(code="NOT_FOUND", message="Registration not found", status_code=404)
    if reg.status not in {ExamRegistrationStatus.SUBMITTED, ExamRegistrationStatus.CONFIRMED, ExamRegistrationStatus.CORRECTION_PENDING}:
        raise AppError(code="REGISTRATION_LOCKED", message="Registration cannot be corrected", status_code=409)
    if payload.subjects is not None:
        await ExamRegistrationSubject.find(
            Eq(ExamRegistrationSubject.tenant_id, tenant_id),
            Eq(ExamRegistrationSubject.registration_id, registration_id),
        ).delete()
        for subject in payload.subjects:
            await ExamRegistrationSubject(
                tenant_id=tenant_id,
                registration_id=registration_id,
                student_user_id=reg.student_user_id,
                exam_session_id=reg.exam_session_id,
                course_code=subject.course_code,
                subject_code=subject.subject_code,
                paper_code=subject.paper_code,
                subject_type=subject.subject_type,
            ).insert()
    reg.status = ExamRegistrationStatus.CORRECTION_PENDING
    reg.updated_at = utcnow()
    await reg.save()
    await _write_history(
        tenant_id,
        registration_id=registration_id,
        exam_session_id=reg.exam_session_id,
        student_user_id=reg.student_user_id,
        action=ExamRegistrationHistoryAction.CORRECTION_REQUESTED,
        actor_id=actor.id,
        note=payload.note,
    )
    return await _read_registration(tenant_id, registration_id)


async def get_registration(scope: AccessScope, actor: User, registration_id: str) -> ExamRegistrationRead:
    if actor.id and Permission.STUDENT_EXAM_REGISTRATION_READ in scope.effective_permissions:
        tenant_id = require_student_scope(scope)
    else:
        authorize(scope, Permission.EXAMINATION_CELL_REGISTRATION_READ)
        tenant_id = require_examination_cell_tenant(scope)
    reg = await ExamRegistration.find_one(Eq(ExamRegistration.tenant_id, tenant_id), Eq(ExamRegistration.registration_id, registration_id))
    if reg is None:
        raise AppError(code="NOT_FOUND", message="Registration not found", status_code=404)
    if actor.id != reg.student_user_id:
        authorize(scope, Permission.EXAMINATION_CELL_REGISTRATION_READ)
    return await _read_registration(tenant_id, registration_id)


async def list_registrations_for_session(
    scope: AccessScope,
    exam_session_id: PydanticObjectId,
    pagination: Pagination,
) -> Page[ExamRegistrationRead]:
    authorize(scope, Permission.EXAMINATION_CELL_REGISTRATION_READ)
    tenant_id = require_examination_cell_tenant(scope)
    query = ExamRegistration.find(Eq(ExamRegistration.tenant_id, tenant_id), Eq(ExamRegistration.exam_session_id, exam_session_id))
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    items = [await _read_registration(tenant_id, r.registration_id) for r in rows]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def registration_summary(scope: AccessScope, exam_session_id: PydanticObjectId) -> ExamRegistrationSummaryRead:
    authorize(scope, Permission.EXAMINATION_CELL_REGISTRATION_READ)
    tenant_id = require_examination_cell_tenant(scope)
    base = {"tenant_id": tenant_id, "exam_session_id": exam_session_id}
    total = await ExamRegistration.find(base).count()
    confirmed = await ExamRegistration.find({**base, "status": ExamRegistrationStatus.CONFIRMED.value}).count()
    submitted = await ExamRegistration.find({**base, "status": ExamRegistrationStatus.SUBMITTED.value}).count()
    cancelled = await ExamRegistration.find({**base, "status": ExamRegistrationStatus.CANCELLED.value}).count()
    pending_fee = await ExamRegistration.find({**base, "fee_verified": False, "status": {"$nin": [ExamRegistrationStatus.CANCELLED.value]}}).count()
    return ExamRegistrationSummaryRead(
        exam_session_id=str(exam_session_id),
        total_registrations=total,
        confirmed=confirmed,
        submitted=submitted,
        cancelled=cancelled,
        pending_fee=pending_fee,
    )


async def registration_history(
    scope: AccessScope,
    registration_id: str,
    pagination: Pagination,
) -> Page[ExamRegistrationHistoryRead]:
    tenant_id = require_examination_cell_tenant(scope)
    query = ExamRegistrationHistory.find(
        Eq(ExamRegistrationHistory.tenant_id, tenant_id),
        Eq(ExamRegistrationHistory.registration_id, registration_id),
    ).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        ExamRegistrationHistoryRead(
            registration_id=r.registration_id,
            action=r.action.value,
            actor_id=str(r.actor_id) if r.actor_id else None,
            note=r.note,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)