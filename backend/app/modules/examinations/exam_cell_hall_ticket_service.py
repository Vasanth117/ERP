"""Examination cell — hall ticket generation and verification."""

import hashlib
import hmac
import secrets
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_audit import record_exam_activity
from app.modules.examinations.exam_cell_hall_ticket_models import ExamHallTicket, ExamHallTicketHistory, ExamHallTicketSubject
from app.modules.examinations.exam_cell_hall_ticket_pdf import build_hall_ticket_pdf
from app.modules.examinations.exam_cell_hall_ticket_schemas import (
    ExamHallTicketBulkGenerateRequest,
    ExamHallTicketGenerateRequest,
    ExamHallTicketHistoryRead,
    ExamHallTicketRead,
    ExamHallTicketReissueRequest,
    ExamHallTicketSubjectRead,
    ExamHallTicketVerifyRequest,
    ExamHallTicketVerifyResponse,
)
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_policy import (
    authorize_examination_cell_hall_ticket_manage,
    authorize_examination_cell_hall_ticket_publish,
    require_examination_cell_tenant,
)
from app.modules.examinations.exam_cell_registration_enums import (
    ExamHallTicketHistoryAction,
    ExamHallTicketStatus,
    ExamRegistrationStatus,
)
from app.modules.examinations.exam_cell_registration_models import ExamEligibilityRecord, ExamRegistration, ExamRegistrationSubject
from app.modules.examinations.exam_cell_timetable_enums import ExamTimetableEntryStatus, ExamTimetableStatus
from app.modules.examinations.exam_cell_timetable_models import ExamTimetable, ExamTimetableEntry
from app.modules.lms.storage import read_bytes, storage_key_for, write_bytes
from app.modules.students.models import StudentProfile
from app.modules.tenants.models import Tenant


def _hall_ticket_id() -> str:
    return f"eht_{uuid4().hex[:10]}"


def _ticket_number() -> str:
    return f"EHT-{uuid4().hex[:10].upper()}"


def _verification_code(ticket_number: str, student_id: PydanticObjectId) -> str:
    secret = get_settings().jwt_secret.encode()
    digest = hmac.new(secret, f"{ticket_number}:{student_id}".encode(), hashlib.sha256).hexdigest()
    return digest[:20].upper()


async def _assert_registration(
    tenant_id: PydanticObjectId,
    student_id: PydanticObjectId,
    session_id: PydanticObjectId,
) -> ExamRegistration:
    reg = await ExamRegistration.find_one(
        {
            "tenant_id": tenant_id,
            "student_user_id": student_id,
            "exam_session_id": session_id,
            "status": {
                "$in": [
                    ExamRegistrationStatus.SUBMITTED.value,
                    ExamRegistrationStatus.CONFIRMED.value,
                ]
            },
        }
    )
    if reg is None:
        raise AppError(code="NOT_REGISTERED", message="Student is not registered for this session", status_code=403)
    eligibility = await ExamEligibilityRecord.find_one(
        Eq(ExamEligibilityRecord.tenant_id, tenant_id),
        Eq(ExamEligibilityRecord.student_user_id, student_id),
        Eq(ExamEligibilityRecord.exam_session_id, session_id),
    )
    if eligibility is None or not eligibility.overall_eligible:
        raise AppError(code="NOT_ELIGIBLE", message="Student is not eligible for hall ticket", status_code=403)
    return reg


async def _schedule_lines(
    tenant_id: PydanticObjectId,
    session_id: PydanticObjectId,
    course_codes: set[str],
) -> dict[str, ExamTimetableEntry]:
    timetable = await ExamTimetable.find_one(
        {
            "tenant_id": tenant_id,
            "exam_session_id": session_id,
            "status": ExamTimetableStatus.PUBLISHED.value,
        }
    )
    if timetable is None:
        return {}
    entries = await ExamTimetableEntry.find(
        {
            "tenant_id": tenant_id,
            "timetable_id": timetable.id,
            "status": ExamTimetableEntryStatus.ACTIVE.value,
            "course_code": {"$in": list(course_codes)},
        }
    ).to_list()
    return {e.course_code: e for e in entries}


async def _ticket_read(tenant_id: PydanticObjectId, doc: ExamHallTicket) -> ExamHallTicketRead:
    subjects = await ExamHallTicketSubject.find(
        Eq(ExamHallTicketSubject.tenant_id, tenant_id),
        Eq(ExamHallTicketSubject.hall_ticket_id, doc.hall_ticket_id),
    ).to_list()
    return ExamHallTicketRead(
        hall_ticket_id=doc.hall_ticket_id,
        ticket_number=doc.ticket_number,
        verification_code=doc.verification_code,
        exam_session_id=str(doc.exam_session_id),
        season_id=doc.season_id,
        registration_id=doc.registration_id,
        student_user_id=str(doc.student_user_id),
        institution_name=doc.institution_name,
        roll_number=doc.roll_number,
        student_name=doc.student_name,
        status=doc.status,
        subjects=[
            ExamHallTicketSubjectRead(
                course_code=s.course_code,
                subject_code=s.subject_code,
                paper_code=s.paper_code,
                scheduled_start=s.scheduled_start,
                scheduled_end=s.scheduled_end,
                centre_code=s.centre_code,
                room_label=s.room_label,
                facility_id=s.facility_id,
            )
            for s in subjects
        ],
        published_at=doc.published_at,
        has_pdf=bool(doc.storage_key),
    )


async def _history(tenant_id: PydanticObjectId, hall_ticket_id: str, action: ExamHallTicketHistoryAction, actor_id: PydanticObjectId | None, note: str | None = None) -> None:
    await ExamHallTicketHistory(
        tenant_id=tenant_id,
        hall_ticket_id=hall_ticket_id,
        action=action,
        actor_id=actor_id,
        note=note,
    ).insert()


async def generate_hall_ticket(
    scope: AccessScope,
    actor: User,
    payload: ExamHallTicketGenerateRequest,
) -> ExamHallTicketRead:
    authorize_examination_cell_hall_ticket_manage(scope)
    tenant_id = require_examination_cell_tenant(scope)
    session_id = to_object_id(payload.exam_session_id, "exam_session_id")
    student_id = to_object_id(payload.student_user_id, "student_user_id")
    session = await ExamSession.find_one(Eq(ExamSession.tenant_id, tenant_id), Eq(ExamSession.id, session_id))
    if session is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)
    reg = await _assert_registration(tenant_id, student_id, session_id)
    existing = await ExamHallTicket.find_one(
        {
            "tenant_id": tenant_id,
            "student_user_id": student_id,
            "exam_session_id": session_id,
            "status": {"$nin": [ExamHallTicketStatus.REVOKED.value]},
        }
    )
    if existing and existing.status in {ExamHallTicketStatus.GENERATED, ExamHallTicketStatus.PUBLISHED}:
        raise AppError(code="HALL_TICKET_EXISTS", message="Hall ticket already generated", status_code=409)

    reg_subjects = await ExamRegistrationSubject.find(
        Eq(ExamRegistrationSubject.tenant_id, tenant_id),
        Eq(ExamRegistrationSubject.registration_id, reg.registration_id),
    ).to_list()
    course_codes = {s.course_code for s in reg_subjects}
    schedule_map = await _schedule_lines(tenant_id, session_id, course_codes)

    profile = await StudentProfile.find_one({"tenant_id": tenant_id, "user_id": student_id})
    student_user = await User.get(student_id)
    tenant = await Tenant.get(tenant_id)
    ticket_number = _ticket_number()
    hall_ticket_id = _hall_ticket_id()
    verification = _verification_code(ticket_number, student_id)

    doc = ExamHallTicket(
        tenant_id=tenant_id,
        hall_ticket_id=hall_ticket_id,
        ticket_number=ticket_number,
        verification_code=verification,
        exam_session_id=session_id,
        season_id=session.season_id,
        registration_id=reg.registration_id,
        student_user_id=student_id,
        institution_name=tenant.name if tenant else None,
        roll_number=profile.roll_number if profile else None,
        student_name=student_user.full_name if student_user else None,
        status=ExamHallTicketStatus.GENERATED,
        document_token=secrets.token_urlsafe(24),
        created_by=actor.id,
    )
    subject_lines: list[str] = []
    for subj in reg_subjects:
        entry = schedule_map.get(subj.course_code)
        await ExamHallTicketSubject(
            tenant_id=tenant_id,
            hall_ticket_id=hall_ticket_id,
            course_code=subj.course_code,
            subject_code=subj.subject_code,
            paper_code=subj.paper_code,
            scheduled_start=entry.scheduled_start if entry else None,
            scheduled_end=entry.scheduled_end if entry else None,
            centre_code=entry.centre_code if entry else None,
            room_label=entry.room_label if entry else None,
            facility_id=entry.facility_id if entry else None,
        ).insert()
        when = ""
        if entry:
            when = f" {entry.scheduled_start.isoformat()}"
        venue = ""
        if entry and entry.centre_code and entry.room_label:
            venue = f" @ {entry.centre_code}/{entry.room_label}"
        subject_lines.append(f"{subj.course_code}{when}{venue}")

    pdf = build_hall_ticket_pdf(
        institution_name=doc.institution_name or "Institution",
        ticket_number=ticket_number,
        student_name=doc.student_name or "Student",
        roll_number=doc.roll_number or "—",
        session_title=session.name,
        subjects=subject_lines,
        verification_code=verification,
    )
    key = storage_key_for(str(tenant_id), "exam_hall_tickets", f"{ticket_number}.pdf")
    storage_key, checksum = write_bytes(key, pdf)
    doc.storage_key = storage_key
    doc.payload_checksum = checksum
    await doc.insert()
    await _history(tenant_id, hall_ticket_id, ExamHallTicketHistoryAction.GENERATED, actor.id)

    if payload.publish:
        return await publish_hall_ticket(scope, actor, hall_ticket_id)

    await record_exam_activity(
        tenant_id,
        actor_id=actor.id,
        action="exam_hall_ticket.generated",
        summary=f"Hall ticket {ticket_number}",
        exam_session_id=session_id,
        season_id=session.season_id,
    )
    return await _ticket_read(tenant_id, doc)


async def bulk_generate_hall_tickets(
    scope: AccessScope,
    actor: User,
    payload: ExamHallTicketBulkGenerateRequest,
) -> list[ExamHallTicketRead]:
    authorize_examination_cell_hall_ticket_manage(scope)
    results: list[ExamHallTicketRead] = []
    for sid in payload.student_user_ids:
        single = ExamHallTicketGenerateRequest(
            exam_session_id=payload.exam_session_id,
            student_user_id=sid,
            publish=payload.publish,
        )
        try:
            results.append(await generate_hall_ticket(scope, actor, single))
        except AppError as exc:
            if exc.code in {"HALL_TICKET_EXISTS", "NOT_REGISTERED", "NOT_ELIGIBLE"}:
                continue
            raise
    return results


async def publish_hall_ticket(scope: AccessScope, actor: User, hall_ticket_id: str) -> ExamHallTicketRead:
    authorize_examination_cell_hall_ticket_publish(scope)
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamHallTicket.find_one(
        Eq(ExamHallTicket.tenant_id, tenant_id),
        Eq(ExamHallTicket.hall_ticket_id, hall_ticket_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Hall ticket not found", status_code=404)
    if doc.status == ExamHallTicketStatus.REVOKED:
        raise AppError(code="HALL_TICKET_REVOKED", message="Hall ticket is revoked", status_code=409)
    doc.status = ExamHallTicketStatus.PUBLISHED
    doc.published_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save()
    await _history(tenant_id, hall_ticket_id, ExamHallTicketHistoryAction.PUBLISHED, actor.id)
    from app.modules.examinations.exam_cell_models import ExamSession
    from app.modules.examinations.exam_cell_notification_triggers import notify_hall_ticket_available

    session = await ExamSession.get(doc.exam_session_id)
    await notify_hall_ticket_available(
        tenant_id,
        student_user_id=doc.student_user_id,
        exam_session_id=doc.exam_session_id,
        session_name=session.name if session else hall_ticket_id,
        hall_ticket_id=hall_ticket_id,
    )
    return await _ticket_read(tenant_id, doc)


async def revoke_hall_ticket(scope: AccessScope, actor: User, hall_ticket_id: str, note: str | None = None) -> ExamHallTicketRead:
    authorize_examination_cell_hall_ticket_publish(scope)
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamHallTicket.find_one(
        Eq(ExamHallTicket.tenant_id, tenant_id),
        Eq(ExamHallTicket.hall_ticket_id, hall_ticket_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Hall ticket not found", status_code=404)
    doc.status = ExamHallTicketStatus.REVOKED
    doc.revoked_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save()
    await _history(tenant_id, hall_ticket_id, ExamHallTicketHistoryAction.REVOKED, actor.id, note=note)
    return await _ticket_read(tenant_id, doc)


async def reissue_hall_ticket(
    scope: AccessScope,
    actor: User,
    hall_ticket_id: str,
    payload: ExamHallTicketReissueRequest,
) -> ExamHallTicketRead:
    authorize_examination_cell_hall_ticket_manage(scope)
    tenant_id = require_examination_cell_tenant(scope)
    old = await ExamHallTicket.find_one(
        Eq(ExamHallTicket.tenant_id, tenant_id),
        Eq(ExamHallTicket.hall_ticket_id, hall_ticket_id),
    )
    if old is None:
        raise AppError(code="NOT_FOUND", message="Hall ticket not found", status_code=404)
    await revoke_hall_ticket(scope, actor, hall_ticket_id, note="Revoked for reissue")
    return await generate_hall_ticket(
        scope,
        actor,
        ExamHallTicketGenerateRequest(
            exam_session_id=str(old.exam_session_id),
            student_user_id=str(old.student_user_id),
            publish=False,
        ),
    )


async def get_hall_ticket(scope: AccessScope, hall_ticket_id: str) -> ExamHallTicketRead:
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamHallTicket.find_one(
        Eq(ExamHallTicket.tenant_id, tenant_id),
        Eq(ExamHallTicket.hall_ticket_id, hall_ticket_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Hall ticket not found", status_code=404)
    return await _ticket_read(tenant_id, doc)


async def download_hall_ticket_pdf(scope: AccessScope, actor: User, hall_ticket_id: str) -> tuple[bytes, str]:
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamHallTicket.find_one(
        Eq(ExamHallTicket.tenant_id, tenant_id),
        Eq(ExamHallTicket.hall_ticket_id, hall_ticket_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Hall ticket not found", status_code=404)
    if doc.student_user_id != actor.id:
        authorize_examination_cell_hall_ticket_manage(scope)
    if doc.status != ExamHallTicketStatus.PUBLISHED:
        raise AppError(code="FORBIDDEN", message="Hall ticket is not published", status_code=403)
    if not doc.storage_key:
        raise AppError(code="NOT_AVAILABLE", message="PDF not available", status_code=503)
    await _history(tenant_id, hall_ticket_id, ExamHallTicketHistoryAction.DOWNLOADED, actor.id)
    data = read_bytes(doc.storage_key)
    return data, f"hall-ticket-{doc.ticket_number}.pdf"


async def verify_hall_ticket(scope: AccessScope, payload: ExamHallTicketVerifyRequest) -> ExamHallTicketVerifyResponse:
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamHallTicket.find_one(
        Eq(ExamHallTicket.tenant_id, tenant_id),
        Eq(ExamHallTicket.ticket_number, payload.ticket_number.strip().upper()),
    )
    if doc is None:
        return ExamHallTicketVerifyResponse(valid=False, message="Hall ticket not found")
    expected = _verification_code(doc.ticket_number, doc.student_user_id)
    if not hmac.compare_digest(expected, payload.verification_code.strip().upper()):
        return ExamHallTicketVerifyResponse(valid=False, message="Verification code mismatch")
    if doc.status == ExamHallTicketStatus.REVOKED:
        return ExamHallTicketVerifyResponse(valid=False, status=doc.status, message="Hall ticket revoked")
    return ExamHallTicketVerifyResponse(
        valid=doc.status == ExamHallTicketStatus.PUBLISHED,
        status=doc.status,
        student_name=doc.student_name,
        exam_session_id=str(doc.exam_session_id),
        message="Valid published hall ticket" if doc.status == ExamHallTicketStatus.PUBLISHED else "Not published",
    )


async def hall_ticket_history(scope: AccessScope, hall_ticket_id: str) -> list[ExamHallTicketHistoryRead]:
    tenant_id = require_examination_cell_tenant(scope)
    rows = await ExamHallTicketHistory.find(
        Eq(ExamHallTicketHistory.tenant_id, tenant_id),
        Eq(ExamHallTicketHistory.hall_ticket_id, hall_ticket_id),
    ).sort("-created_at").to_list()
    return [
        ExamHallTicketHistoryRead(
            action=r.action.value,
            actor_id=str(r.actor_id) if r.actor_id else None,
            note=r.note,
            created_at=r.created_at,
        )
        for r in rows
    ]