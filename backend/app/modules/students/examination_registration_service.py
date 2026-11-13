"""Examination registration and hall ticket portal."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
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
from app.modules.examinations.examination_registration_enums import HallTicketPublicationStatus
from app.modules.students.examination_registration_enums import (
    ExamRegistrationHistoryAction,
    ExamRegistrationSubjectType,
    StudentExamRegistrationStatus,
)
from app.modules.students.examination_registration_models import (
    StudentExamRegistration,
    StudentExamRegistrationHistory,
    StudentExamRegistrationSubject,
    StudentHallTicketDownloadLog,
    StudentHallTicketReference,
)
from app.modules.students.examination_registration_schemas import (
    EligibleExaminationRead,
    EligibleExamSubjectRead,
    ExamRegistrationHistoryRead,
    ExamRegistrationRead,
    ExamRegistrationSubmitInput,
    ExaminationRegistrationEligibilityRead,
    ExaminationRegistrationScheduleRead,
    HallTicketAvailabilityRead,
    HallTicketDetailsRead,
    HallTicketDownloadRead,
)
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.integrations.examination_registration_reader import (
    fee_payment,
    fee_verified,
    published_hall_ticket,
    published_season,
    registration_window,
    student_eligibility,
    window_open,
)
from app.modules.students.integrations.semester_examination_reader import published_seasons
from app.modules.students.policy import require_student_scope
from app.modules.students.profile_service import ensure_student_profile

_reader = StudentDataReader()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _term(tenant_id: PydanticObjectId) -> tuple[str, str]:
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    return context.academic_year_label, context.semester_label


async def _eligible_subjects_for_student(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId, season_id: str, year: str, semester: str
) -> list[EligibleExamSubjectRead]:
    eligibility = await student_eligibility(tenant_id, user_id, season_id)
    active_regs = await StudentExamRegistration.find(
        {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "season_id": season_id,
            "status": {"$nin": [StudentExamRegistrationStatus.CANCELLED, StudentExamRegistrationStatus.REJECTED]},
        }
    ).to_list()
    reg_ids = {r.registration_id for r in active_regs}
    registered_codes: set[str] = set()
    if reg_ids:
        registered_codes = {
            s.course_code
            for s in await StudentExamRegistrationSubject.find(
                {"tenant_id": tenant_id, "registration_id": {"$in": list(reg_ids)}}
            ).to_list()
        }
    items: list[EligibleExamSubjectRead] = []
    if eligibility and eligibility.semester_course_codes:
        codes = eligibility.semester_course_codes
    else:
        roster = await _reader.roster_entries(tenant_id, user_id, academic_year_label=year, semester_label=semester)
        codes = [r.course_code for r in roster]
    for code in codes:
        items.append(
            EligibleExamSubjectRead(
                course_code=code,
                subject_type=ExamRegistrationSubjectType.SEMESTER,
                already_registered=code in registered_codes,
            )
        )
    if eligibility and eligibility.arrear_course_codes:
        for code in eligibility.arrear_course_codes:
            items.append(
                EligibleExamSubjectRead(
                    course_code=code,
                    subject_type=ExamRegistrationSubjectType.ARREAR,
                    already_registered=code in registered_codes,
                )
            )
    return items


async def list_eligible_examinations(scope: AccessScope, user: User) -> list[EligibleExaminationRead]:
    authorize(scope, Permission.STUDENT_EXAM_REGISTRATION_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    seasons = await published_seasons(tenant_id, year=year, semester=semester)
    rows: list[EligibleExaminationRead] = []
    for season in seasons:
        window = await registration_window(tenant_id, season.season_id)
        eligibility = await student_eligibility(tenant_id, user.id, season.season_id)
        rows.append(
            EligibleExaminationRead(
                season_id=season.season_id,
                title=season.title,
                academic_year_label=season.academic_year_label,
                semester_label=season.semester_label,
                registration_open_at=window.registration_open_at if window else None,
                registration_close_at=window.registration_close_at if window else None,
                registration_open=window_open(window),
                eligible=bool(eligibility and eligibility.eligible),
            )
        )
    return rows


async def get_registration_schedule(scope: AccessScope, user: User, season_id: str) -> ExaminationRegistrationScheduleRead:
    authorize(scope, Permission.STUDENT_EXAM_REGISTRATION_READ)
    tenant_id = require_student_scope(scope)
    if await published_season(tenant_id, season_id) is None:
        raise AppError(code="NOT_FOUND", message="Examination season not found", status_code=404)
    window = await registration_window(tenant_id, season_id)
    if window is None:
        raise AppError(code="NOT_FOUND", message="Registration schedule not published", status_code=404)
    return ExaminationRegistrationScheduleRead(
        season_id=season_id,
        registration_open_at=window.registration_open_at,
        registration_close_at=window.registration_close_at,
        cancellation_deadline=window.cancellation_deadline,
        fee_required=window.fee_required,
        fee_amount=window.fee_amount,
        fee_code=window.fee_code,
        allow_arrear_registration=window.allow_arrear_registration,
    )


async def validate_registration_eligibility(scope: AccessScope, user: User, season_id: str) -> ExaminationRegistrationEligibilityRead:
    authorize(scope, Permission.STUDENT_EXAM_REGISTRATION_READ)
    tenant_id = require_student_scope(scope)
    window = await registration_window(tenant_id, season_id)
    eligibility = await student_eligibility(tenant_id, user.id, season_id)
    reasons: list[str] = []
    if eligibility is None:
        reasons.append("Examination eligibility not published")
    elif not eligibility.eligible:
        reasons.extend(eligibility.reasons or ["Not eligible for examinations"])
    if not window_open(window):
        reasons.append("Registration window is closed")
    payment = await fee_payment(tenant_id, user.id, season_id, window.fee_code) if window else None
    fee_ok = fee_verified(payment, fee_required=window.fee_required if window else False)
    if window and window.fee_required and not fee_ok:
        reasons.append("Examination fee not verified")
    return ExaminationRegistrationEligibilityRead(
        season_id=season_id,
        eligible=not reasons and bool(eligibility and eligibility.eligible),
        reasons=reasons,
        fee_payment_status=payment.status.value if payment else None,
        fee_verified=fee_ok,
        registration_window_open=window_open(window),
    )


async def get_eligible_subjects(scope: AccessScope, user: User, season_id: str) -> list[EligibleExamSubjectRead]:
    authorize(scope, Permission.STUDENT_EXAM_REGISTRATION_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    return await _eligible_subjects_for_student(tenant_id, user.id, season_id, year, semester)


async def _write_history(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    registration_id: str,
    season_id: str,
    action: ExamRegistrationHistoryAction,
    note: str | None = None,
) -> None:
    await StudentExamRegistrationHistory(
        tenant_id=tenant_id,
        user_id=user_id,
        registration_id=registration_id,
        season_id=season_id,
        action=action,
        note=note,
        actor_user_id=user_id,
    ).insert()


async def submit_examination_registration(
    scope: AccessScope, user: User, payload: ExamRegistrationSubmitInput
) -> ExamRegistrationRead:
    authorize(scope, Permission.STUDENT_EXAM_REGISTRATION_MANAGE)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    validation = await validate_registration_eligibility(scope, user, payload.season_id)
    if not validation.eligible:
        raise AppError(
            code="REGISTRATION_NOT_ELIGIBLE",
            message="; ".join(validation.reasons) or "Not eligible",
            status_code=403,
        )
    window = await registration_window(tenant_id, payload.season_id)
    if window is None or not window_open(window):
        raise AppError(code="REGISTRATION_CLOSED", message="Registration window closed", status_code=403)
    allowed = await get_eligible_subjects(scope, user, payload.season_id)
    allowed_map = {(s.course_code, s.subject_type): s for s in allowed}
    for subject in payload.subjects:
        key = (subject.course_code, subject.subject_type)
        if key not in allowed_map:
            raise AppError(code="INVALID_SUBJECT", message=f"Subject {subject.course_code} is not eligible", status_code=422)
        if allowed_map[key].already_registered:
            raise AppError(code="DUPLICATE_REGISTRATION", message=f"Already registered for {subject.course_code}", status_code=409)
    payment = await fee_payment(tenant_id, user.id, payload.season_id, window.fee_code)
    if not fee_verified(payment, fee_required=window.fee_required):
        raise AppError(code="FEE_NOT_VERIFIED", message="Examination fee payment not verified", status_code=402)
    registration_id = f"ereg-{uuid4().hex[:12]}"
    reg = StudentExamRegistration(
        tenant_id=tenant_id,
        user_id=user.id,
        season_id=payload.season_id,
        registration_id=registration_id,
        academic_year_label=year,
        semester_label=semester,
        status=StudentExamRegistrationStatus.SUBMITTED,
        fee_verified=True,
        submitted_at=_utcnow(),
    )
    await reg.insert()
    try:
        for subject in payload.subjects:
            await StudentExamRegistrationSubject(
                tenant_id=tenant_id,
                registration_id=registration_id,
                user_id=user.id,
                season_id=payload.season_id,
                course_code=subject.course_code,
                subject_type=subject.subject_type,
                paper_code=subject.paper_code,
            ).insert()
    except DuplicateKeyError as exc:
        await reg.delete()
        raise AppError(code="DUPLICATE_REGISTRATION", message="Duplicate examination registration", status_code=409) from exc
    await _write_history(tenant_id, user.id, registration_id, payload.season_id, ExamRegistrationHistoryAction.SUBMITTED)
    await record_audit(
        actor_id=scope.user_id,
        action="student.exam_registration.submitted",
        resource_type="student_exam_registration",
        resource_id=registration_id,
        tenant_id=tenant_id,
    )
    return await get_registration_status(scope, user, registration_id)


async def get_registration_status(scope: AccessScope, user: User, registration_id: str) -> ExamRegistrationRead:
    authorize(scope, Permission.STUDENT_EXAM_REGISTRATION_READ)
    tenant_id = require_student_scope(scope)
    reg = await StudentExamRegistration.find_one(
        {"tenant_id": tenant_id, "user_id": user.id, "registration_id": registration_id}
    )
    if reg is None:
        raise AppError(code="NOT_FOUND", message="Registration not found", status_code=404)
    subjects = await StudentExamRegistrationSubject.find({"tenant_id": tenant_id, "registration_id": registration_id}).to_list()
    return ExamRegistrationRead(
        registration_id=reg.registration_id,
        season_id=reg.season_id,
        status=reg.status,
        fee_verified=reg.fee_verified,
        subjects=[
            EligibleExamSubjectRead(course_code=s.course_code, subject_type=s.subject_type, paper_code=s.paper_code)
            for s in subjects
        ],
        submitted_at=reg.submitted_at,
        cancelled_at=reg.cancelled_at,
        created_at=reg.created_at,
    )


async def list_registrations(scope: AccessScope, user: User, season_id: str | None = None) -> list[ExamRegistrationRead]:
    authorize(scope, Permission.STUDENT_EXAM_REGISTRATION_READ)
    tenant_id = require_student_scope(scope)
    filters: dict = {"tenant_id": tenant_id, "user_id": user.id}
    if season_id:
        filters["season_id"] = season_id
    regs = await StudentExamRegistration.find(filters).sort("-created_at").to_list()
    results: list[ExamRegistrationRead] = []
    for reg in regs:
        results.append(await get_registration_status(scope, user, reg.registration_id))
    return results


async def cancel_registration(scope: AccessScope, user: User, registration_id: str) -> ExamRegistrationRead:
    authorize(scope, Permission.STUDENT_EXAM_REGISTRATION_MANAGE)
    tenant_id = require_student_scope(scope)
    reg = await StudentExamRegistration.find_one(
        {"tenant_id": tenant_id, "user_id": user.id, "registration_id": registration_id}
    )
    if reg is None:
        raise AppError(code="NOT_FOUND", message="Registration not found", status_code=404)
    if reg.status == StudentExamRegistrationStatus.CANCELLED:
        raise AppError(code="ALREADY_CANCELLED", message="Registration already cancelled", status_code=409)
    window = await registration_window(tenant_id, reg.season_id)
    now = _utcnow()
    if window and window.cancellation_deadline and now > window.cancellation_deadline:
        raise AppError(code="CANCELLATION_CLOSED", message="Cancellation deadline passed", status_code=403)
    reg.status = StudentExamRegistrationStatus.CANCELLED
    reg.cancelled_at = now
    reg.updated_at = now
    await reg.save()
    await StudentExamRegistrationSubject.find({"tenant_id": tenant_id, "registration_id": registration_id}).delete()
    await _write_history(tenant_id, user.id, registration_id, reg.season_id, ExamRegistrationHistoryAction.CANCELLED)
    await record_audit(
        actor_id=scope.user_id,
        action="student.exam_registration.cancelled",
        resource_type="student_exam_registration",
        resource_id=registration_id,
        tenant_id=tenant_id,
    )
    return await get_registration_status(scope, user, registration_id)


async def registration_history(scope: AccessScope, user: User, pagination: Pagination) -> Page[ExamRegistrationHistoryRead]:
    authorize(scope, Permission.STUDENT_EXAM_REGISTRATION_READ)
    tenant_id = require_student_scope(scope)
    query = StudentExamRegistrationHistory.find({"tenant_id": tenant_id, "user_id": user.id}).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            ExamRegistrationHistoryRead(
                registration_id=r.registration_id,
                season_id=r.season_id,
                action=r.action.value,
                note=r.note,
                created_at=r.created_at,
            )
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def _sync_hall_ticket_ref(tenant_id: PydanticObjectId, user_id: PydanticObjectId, season_id: str) -> StudentHallTicketReference | None:
    ticket = await published_hall_ticket(tenant_id, user_id, season_id)
    if ticket is None:
        return None
    ref = await StudentHallTicketReference.find_one({"tenant_id": tenant_id, "user_id": user_id, "season_id": season_id})
    status = ticket.status.value
    if ref is None:
        ref = StudentHallTicketReference(
            tenant_id=tenant_id,
            user_id=user_id,
            season_id=season_id,
            hall_ticket_id=ticket.id,
            ticket_number=ticket.ticket_number,
            availability_status=status,
        )
        await ref.insert()
    else:
        ref.hall_ticket_id = ticket.id
        ref.ticket_number = ticket.ticket_number
        ref.availability_status = status
        ref.updated_at = _utcnow()
        await ref.save()
    return ref


async def hall_ticket_availability(scope: AccessScope, user: User, season_id: str) -> HallTicketAvailabilityRead:
    authorize(scope, Permission.STUDENT_EXAM_REGISTRATION_READ)
    tenant_id = require_student_scope(scope)
    ticket = await published_hall_ticket(tenant_id, user.id, season_id)
    if ticket is None:
        return HallTicketAvailabilityRead(season_id=season_id, available=False)
    await _sync_hall_ticket_ref(tenant_id, user.id, season_id)
    return HallTicketAvailabilityRead(
        season_id=season_id,
        available=True,
        ticket_number=ticket.ticket_number,
        status=ticket.status.value,
        published_at=ticket.published_at,
    )


async def get_hall_ticket_details(scope: AccessScope, user: User, season_id: str) -> HallTicketDetailsRead:
    authorize(scope, Permission.STUDENT_EXAM_REGISTRATION_READ)
    tenant_id = require_student_scope(scope)
    ticket = await published_hall_ticket(tenant_id, user.id, season_id)
    if ticket is None:
        raise AppError(code="NOT_FOUND", message="Hall ticket not published", status_code=404)
    profile = await ensure_student_profile(scope, user)
    ref = await _sync_hall_ticket_ref(tenant_id, user.id, season_id)
    if ref:
        ref.last_viewed_at = _utcnow()
        await ref.save()
    return HallTicketDetailsRead(
        season_id=season_id,
        ticket_number=ticket.ticket_number,
        roll_number=ticket.roll_number or profile.roll_number,
        student_name=ticket.student_name or user.full_name,
        centre_code=ticket.centre_code,
        centre_name=ticket.centre_name,
        examination_sessions=ticket.examination_sessions,
        instructions=ticket.instructions,
        published_at=ticket.published_at,
    )


async def download_hall_ticket(
    scope: AccessScope,
    user: User,
    season_id: str,
    *,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> HallTicketDownloadRead:
    authorize(scope, Permission.STUDENT_EXAM_REGISTRATION_READ)
    tenant_id = require_student_scope(scope)
    ticket = await published_hall_ticket(tenant_id, user.id, season_id)
    if ticket is None or ticket.status != HallTicketPublicationStatus.PUBLISHED:
        raise AppError(code="FORBIDDEN", message="Hall ticket not authorized", status_code=403)
    if not ticket.document_token:
        raise AppError(code="NOT_AVAILABLE", message="Download not configured", status_code=503)
    digest = hashlib.sha256(f"{ticket.document_token}:{user.id}".encode()).hexdigest()
    download_token = secrets.token_urlsafe(32)
    expires_at = _utcnow() + timedelta(minutes=15)
    await StudentHallTicketDownloadLog(
        tenant_id=tenant_id,
        user_id=user.id,
        season_id=season_id,
        ticket_number=ticket.ticket_number,
        ip_address=ip_address,
        user_agent=user_agent,
    ).insert()
    await record_audit(
        actor_id=scope.user_id,
        action="student.hall_ticket.downloaded",
        resource_type="examination_hall_ticket",
        resource_id=ticket.ticket_number,
        tenant_id=tenant_id,
        metadata={"checksum": digest[:16]},
    )
    return HallTicketDownloadRead(
        season_id=season_id,
        ticket_number=ticket.ticket_number,
        download_token=download_token,
        expires_at=expires_at,
    )
