"""Arrear, supplementary exams, and backlog (read + supplementary registration)."""

from uuid import uuid4

from beanie import PydanticObjectId
from pymongo.errors import DuplicateKeyError

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.students.arrear_backlog_enums import BacklogStatus, SupplementaryRegistrationStatus
from app.modules.students.arrear_backlog_models import (
    StudentArrearReference,
    StudentExamAttemptHistory,
    StudentSupplementaryRegistration,
)
from app.modules.students.arrear_backlog_schemas import (
    ArrearEligibilityRead,
    ArrearSubjectRead,
    BacklogSummaryRead,
    ExamAttemptHistoryRead,
    SupplementaryFeeRead,
    SupplementaryRegistrationInput,
    SupplementaryRegistrationRead,
    SupplementaryResultRead,
    SupplementaryScheduleRead,
)
from app.modules.students.enums import AcademicStanding, ProgressionStatus
from app.modules.examinations.arrear_examination_models import ExaminationAttemptRecord
from app.modules.students.integrations.arrear_examination_reader import (
    arrear_eligibility,
    fee_is_verified,
    pending_arrear_from_results,
    published_attempts,
    published_supplementary_seasons,
    registration_window_open,
    supplementary_fee,
    supplementary_published_results,
)
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.policy import require_student_scope

_reader = StudentDataReader()


async def _term(tenant_id: PydanticObjectId) -> tuple[str, str]:
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    return context.academic_year_label, context.semester_label


async def _sync_arrear_refs(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[StudentArrearReference]:
    pending_codes = await pending_arrear_from_results(tenant_id, user_id)
    attempts = await published_attempts(tenant_id, user_id)
    by_course: dict[str, ExaminationAttemptRecord] = {}
    for att in attempts:
        by_course[att.course_code] = att
    refs: list[StudentArrearReference] = []
    for code in pending_codes:
        ref = await StudentArrearReference.find_one({"tenant_id": tenant_id, "user_id": user_id, "course_code": code})
        att = by_course.get(code)
        if ref is None:
            ref = StudentArrearReference(
                tenant_id=tenant_id,
                user_id=user_id,
                course_code=code,
                backlog_status=BacklogStatus.PENDING,
                last_attempt_season_id=att.season_id if att else None,
                last_outcome=att.outcome if att else "fail",
            )
            await ref.insert()
        refs.append(ref)
    cleared_regs = await StudentSupplementaryRegistration.find(
        {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "status": SupplementaryRegistrationStatus.CONFIRMED,
        }
    ).to_list()
    cleared_codes = {r.course_code for r in cleared_regs}
    for code in cleared_codes:
        ref = await StudentArrearReference.find_one({"tenant_id": tenant_id, "user_id": user_id, "course_code": code})
        if ref and ref.backlog_status != BacklogStatus.CLEARED:
            ref.backlog_status = BacklogStatus.CLEARED
            await ref.save()
    return await StudentArrearReference.find({"tenant_id": tenant_id, "user_id": user_id}).to_list()


async def get_arrear_subjects(scope: AccessScope, user: User) -> list[ArrearSubjectRead]:
    authorize(scope, Permission.STUDENT_ARREAR_READ)
    tenant_id = require_student_scope(scope)
    refs = await _sync_arrear_refs(tenant_id, user.id)
    attempts = await published_attempts(tenant_id, user.id)
    count_by_course: dict[str, int] = {}
    for a in attempts:
        count_by_course[a.course_code] = count_by_course.get(a.course_code, 0) + 1
    return [
        ArrearSubjectRead(
            course_code=r.course_code,
            backlog_status=r.backlog_status.value,
            last_attempt_season_id=r.last_attempt_season_id,
            last_outcome=r.last_outcome,
            attempt_count=count_by_course.get(r.course_code, 0),
        )
        for r in refs
        if r.backlog_status != BacklogStatus.CLEARED
    ]


async def get_attempt_history(scope: AccessScope, user: User, pagination: Pagination) -> Page[ExamAttemptHistoryRead]:
    authorize(scope, Permission.STUDENT_ARREAR_READ)
    tenant_id = require_student_scope(scope)
    central = await published_attempts(tenant_id, user.id)
    for att in central:
        exists = await StudentExamAttemptHistory.find_one(
            {
                "tenant_id": tenant_id,
                "user_id": user.id,
                "course_code": att.course_code,
                "season_id": att.season_id,
                "attempt_number": att.attempt_number,
            }
        )
        if exists is None:
            await StudentExamAttemptHistory(
                tenant_id=tenant_id,
                user_id=user.id,
                course_code=att.course_code,
                season_id=att.season_id,
                attempt_number=att.attempt_number,
                outcome=att.outcome,
                is_supplementary=att.is_supplementary,
                recorded_at=att.published_at or att.updated_at,
            ).insert()
    query = StudentExamAttemptHistory.find({"tenant_id": tenant_id, "user_id": user.id}).sort("-recorded_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            ExamAttemptHistoryRead(
                course_code=r.course_code,
                season_id=r.season_id,
                attempt_number=r.attempt_number,
                outcome=r.outcome,
                is_supplementary=r.is_supplementary,
                recorded_at=r.recorded_at,
            )
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_arrear_eligibility(scope: AccessScope, user: User, supplementary_season_id: str) -> ArrearEligibilityRead:
    authorize(scope, Permission.STUDENT_ARREAR_READ)
    tenant_id = require_student_scope(scope)
    row = await arrear_eligibility(tenant_id, user.id, supplementary_season_id)
    if row is None:
        raise AppError(code="NOT_FOUND", message="Arrear eligibility not published", status_code=404)
    return ArrearEligibilityRead(
        supplementary_season_id=supplementary_season_id,
        eligible=row.eligible,
        arrear_course_codes=row.arrear_course_codes,
        restrictions=row.restrictions,
    )


async def get_supplementary_schedules(scope: AccessScope, user: User) -> list[SupplementaryScheduleRead]:
    authorize(scope, Permission.STUDENT_ARREAR_READ)
    tenant_id = require_student_scope(scope)
    seasons = await published_supplementary_seasons(tenant_id)
    return [
        SupplementaryScheduleRead(
            supplementary_season_id=s.supplementary_season_id,
            title=s.title,
            registration_open_at=s.registration_open_at,
            registration_close_at=s.registration_close_at,
            parent_season_id=s.parent_season_id,
        )
        for s in seasons
    ]


async def get_supplementary_fee(
    scope: AccessScope, user: User, supplementary_season_id: str
) -> SupplementaryFeeRead:
    authorize(scope, Permission.STUDENT_ARREAR_READ)
    tenant_id = require_student_scope(scope)
    season = next((s for s in await published_supplementary_seasons(tenant_id) if s.supplementary_season_id == supplementary_season_id), None)
    if season is None:
        raise AppError(code="NOT_FOUND", message="Supplementary season not found", status_code=404)
    payment = await supplementary_fee(tenant_id, user.id, season, "")
    return SupplementaryFeeRead(
        fee_required=season.fee_required,
        fee_amount=season.fee_amount,
        fee_code=season.fee_code,
        payment_status=payment.status.value if payment else None,
        fee_verified=fee_is_verified(payment, required=season.fee_required),
    )


async def register_supplementary(
    scope: AccessScope, user: User, payload: SupplementaryRegistrationInput
) -> SupplementaryRegistrationRead:
    authorize(scope, Permission.STUDENT_ARREAR_MANAGE)
    tenant_id = require_student_scope(scope)
    season = next(
        (s for s in await published_supplementary_seasons(tenant_id) if s.supplementary_season_id == payload.supplementary_season_id),
        None,
    )
    if season is None:
        raise AppError(code="NOT_FOUND", message="Supplementary season not found", status_code=404)
    if not registration_window_open(season):
        raise AppError(code="REGISTRATION_CLOSED", message="Registration window closed", status_code=403)
    elig = await arrear_eligibility(tenant_id, user.id, payload.supplementary_season_id)
    if elig is None or not elig.eligible or payload.course_code not in elig.arrear_course_codes:
        raise AppError(code="NOT_ELIGIBLE", message="Not eligible for this arrear subject", status_code=403)
    payment = await supplementary_fee(tenant_id, user.id, season, "")
    if not fee_is_verified(payment, required=season.fee_required):
        raise AppError(code="FEE_NOT_VERIFIED", message="Supplementary fee not verified", status_code=402)
    registration_id = f"sup-{uuid4().hex[:12]}"
    attempt_rows = await published_attempts(tenant_id, user.id)
    attempt_no = max((a.attempt_number for a in attempt_rows if a.course_code == payload.course_code), default=0) + 1
    row = StudentSupplementaryRegistration(
        tenant_id=tenant_id,
        user_id=user.id,
        registration_id=registration_id,
        supplementary_season_id=payload.supplementary_season_id,
        course_code=payload.course_code,
        attempt_number=attempt_no,
        status=SupplementaryRegistrationStatus.SUBMITTED,
        fee_verified=True,
    )
    row.submitted_at = row.created_at
    try:
        await row.insert()
    except DuplicateKeyError as exc:
        raise AppError(code="DUPLICATE_REGISTRATION", message="Already registered for supplementary exam", status_code=409) from exc
    ref = await StudentArrearReference.find_one(
        {"tenant_id": tenant_id, "user_id": user.id, "course_code": payload.course_code}
    )
    if ref:
        ref.backlog_status = BacklogStatus.REGISTERED
        await ref.save()
    await record_audit(
        actor_id=scope.user_id,
        action="student.supplementary.registered",
        resource_type="student_supplementary_registration",
        resource_id=registration_id,
        tenant_id=tenant_id,
    )
    return SupplementaryRegistrationRead(
        registration_id=row.registration_id,
        supplementary_season_id=row.supplementary_season_id,
        course_code=row.course_code,
        attempt_number=row.attempt_number,
        status=row.status.value,
        fee_verified=row.fee_verified,
        submitted_at=row.submitted_at,
    )


async def list_supplementary_registrations(scope: AccessScope, user: User) -> list[SupplementaryRegistrationRead]:
    authorize(scope, Permission.STUDENT_ARREAR_READ)
    tenant_id = require_student_scope(scope)
    rows = await StudentSupplementaryRegistration.find({"tenant_id": tenant_id, "user_id": user.id}).sort("-created_at").to_list()
    return [
        SupplementaryRegistrationRead(
            registration_id=r.registration_id,
            supplementary_season_id=r.supplementary_season_id,
            course_code=r.course_code,
            attempt_number=r.attempt_number,
            status=r.status.value,
            fee_verified=r.fee_verified,
            submitted_at=r.submitted_at,
        )
        for r in rows
    ]


async def get_backlog_summary(scope: AccessScope, user: User) -> BacklogSummaryRead:
    authorize(scope, Permission.STUDENT_ARREAR_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    from app.modules.students.models import StudentAcademicRecord

    record = await StudentAcademicRecord.find_one(
        {"tenant_id": tenant_id, "user_id": user.id, "academic_year_label": year, "semester_label": semester}
    )
    restrictions: list[str] = []
    if record and record.progression_status == ProgressionStatus.HELD:
        restrictions.append("Academic progression on hold")
    if record and record.academic_standing == AcademicStanding.SUSPENDED:
        restrictions.append("Account suspended — supplementary registration may be restricted")
    refs = await _sync_arrear_refs(tenant_id, user.id)
    pending = sum(1 for r in refs if r.backlog_status == BacklogStatus.PENDING)
    cleared = sum(1 for r in refs if r.backlog_status == BacklogStatus.CLEARED)
    registered = sum(1 for r in refs if r.backlog_status == BacklogStatus.REGISTERED)
    subjects = await get_arrear_subjects(scope, user)
    return BacklogSummaryRead(
        pending_count=pending,
        cleared_count=cleared,
        registered_count=registered,
        subjects=subjects,
        progression_restrictions=restrictions,
    )


async def get_supplementary_results(scope: AccessScope, user: User, supplementary_season_id: str) -> list[SupplementaryResultRead]:
    authorize(scope, Permission.STUDENT_ARREAR_READ)
    tenant_id = require_student_scope(scope)
    rows = await supplementary_published_results(tenant_id, user.id, supplementary_season_id)
    return [
        SupplementaryResultRead(
            season_id=r.season_id,
            course_code=r.course_code,
            pass_fail=r.pass_fail,
            total_obtained=r.total_obtained,
            total_max=r.total_max,
            published_at=r.published_at,
        )
        for r in rows
    ]
