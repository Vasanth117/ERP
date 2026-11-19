"""Parent examination, results, timetable and calendar (published data only)."""

from datetime import datetime, timezone

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.academics.models import AcademicCalendarEvent
from app.modules.auth.models import User
from app.modules.examinations.examination_registration_enums import SemesterResultPublicationStatus
from app.modules.parents.enums import ParentDataPermission
from app.modules.parents.models import ParentExamDocumentAccessHistory, ParentExamNotification
from app.modules.parents.phase3_schemas import (
    ParentExamCalendarEventRead,
    ParentExaminationOverviewRead,
    ParentExamNotificationRead,
    ParentExamResultStatusRead,
    ParentExamReviewStatusRead,
    ParentExamSessionRead,
    ParentExamTimetableRead,
)
from app.modules.parents.policy import require_parent_scope
from app.modules.parents.relationship_access import require_student_access
from app.modules.parents.student_context import resolve_student_for_parent
from app.modules.students.exam_review_models import StudentRevaluationRequest
from app.modules.students.examination_registration_schemas import HallTicketAvailabilityRead, HallTicketDownloadRead
from app.modules.students.examination_results_schemas import SemesterResultSummaryRead, SubjectWiseMarksRead
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.integrations.examination_registration_reader import (
    published_hall_ticket,
    registration_window,
    window_open,
)
from app.modules.students.integrations.examination_results_reader import (
    published_result_bundle,
    published_subject_marks,
    result_publication_status,
)
from app.modules.students.integrations.semester_examination_reader import (
    published_seasons,
    student_announcements,
    upcoming_sessions_for_student,
)

_reader = StudentDataReader()


async def _exam_term(tenant_id: PydanticObjectId) -> tuple[str, str]:
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    return context.academic_year_label, context.semester_label


async def _sync_exam_notifications(
    tenant_id: PydanticObjectId, parent_user_id: PydanticObjectId, student_user_id: PydanticObjectId, year: str, semester: str
) -> None:
    announcements = await student_announcements(tenant_id, limit=30)
    for ann in announcements[:30]:
        key = f"announcement:{ann.id}"
        existing = await ParentExamNotification.find_one({"tenant_id": tenant_id, "notification_key": key})
        if existing:
            continue
        await ParentExamNotification(
            tenant_id=tenant_id,
            parent_user_id=parent_user_id,
            student_user_id=student_user_id,
            notification_key=key,
            category="announcement",
            title=ann.title,
            body=ann.body,
            source_ref=str(ann.id),
        ).insert()


async def get_examination_overview(
    scope: AccessScope, parent: User, student_user_id: str
) -> ParentExaminationOverviewRead:
    authorize(scope, Permission.PARENT_EXAM_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_EXAM_TIMETABLE)
    year, semester = await _exam_term(tenant_id)
    upcoming = await upcoming_sessions_for_student(
        tenant_id, sid, year=year, semester=semester, from_time=datetime.now(timezone.utc)
    )
    seasons = await published_seasons(tenant_id, year=year, semester=semester)
    season_id = seasons[0].season_id if seasons else None
    reg_open = None
    if season_id:
        win = await registration_window(tenant_id, season_id)
        reg_open = window_open(win)
    await _sync_exam_notifications(tenant_id, parent.id, sid, year, semester)
    return ParentExaminationOverviewRead(
        academic_year_label=year,
        semester_label=semester,
        upcoming_count=len(upcoming),
        next_examination_at=upcoming[0].scheduled_start if upcoming else None,
        registration_open=reg_open,
        primary_season_id=season_id,
    )


async def get_examination_timetable(
    scope: AccessScope,
    parent: User,
    student_user_id: str,
    *,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> ParentExamTimetableRead:
    authorize(scope, Permission.PARENT_EXAM_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_EXAM_TIMETABLE)
    if academic_year_label and semester_label:
        year, semester = academic_year_label, semester_label
    else:
        year, semester = await _exam_term(tenant_id)
    sessions = await upcoming_sessions_for_student(tenant_id, sid, year=year, semester=semester)
    reads = [
        ParentExamSessionRead(
            session_code=s.session_code,
            season_id=s.season_id,
            course_code=s.course_code,
            section=s.section,
            title=s.course_name or s.course_code,
            scheduled_start=s.scheduled_start,
            scheduled_end=s.scheduled_end,
            venue=s.room or s.centre_code,
            instructions=s.instructions,
        )
        for s in sessions
    ]
    return ParentExamTimetableRead(academic_year_label=year, semester_label=semester, sessions=reads)


async def list_exam_notifications(
    scope: AccessScope, parent: User, student_user_id: str
) -> list[ParentExamNotificationRead]:
    authorize(scope, Permission.PARENT_EXAM_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_EXAM_TIMETABLE)
    rows = await ParentExamNotification.find(
        {"tenant_id": tenant_id, "parent_user_id": parent.id, "student_user_id": sid}
    ).sort("-created_at").limit(50).to_list()
    return [
        ParentExamNotificationRead(
            notification_id=str(r.id),
            category=r.category,
            title=r.title,
            body=r.body,
            read=r.read_at is not None,
            created_at=r.created_at,
        )
        for r in rows
    ]


async def get_published_results_summary(
    scope: AccessScope, parent: User, student_user_id: str, season_id: str
) -> SemesterResultSummaryRead:
    authorize(scope, Permission.PARENT_EXAM_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_RESULTS)
    bundle = await published_result_bundle(tenant_id, sid, season_id)
    if bundle is None:
        raise AppError(code="NOT_FOUND", message="Published results not available", status_code=404)
    return SemesterResultSummaryRead(
        season_id=bundle.season_id,
        academic_year_label=bundle.academic_year_label,
        semester_label=bundle.semester_label,
        overall_pass=bundle.overall_pass,
        gpa=bundle.gpa,
        published_at=bundle.published_at,
        status=bundle.status.value,
    )


async def get_subject_wise_published_results(
    scope: AccessScope, parent: User, student_user_id: str, season_id: str | None = None
) -> list[SubjectWiseMarksRead]:
    authorize(scope, Permission.PARENT_EXAM_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_RESULTS)
    rows = await published_subject_marks(tenant_id, sid, season_id=season_id)
    return [
        SubjectWiseMarksRead(
            season_id=r.season_id,
            course_code=r.course_code,
            course_name=r.course_name,
            attempt_number=r.attempt_number,
            is_arrear=r.is_arrear,
            theory_obtained=r.theory_obtained,
            theory_max=r.theory_max,
            practical_obtained=r.practical_obtained,
            practical_max=r.practical_max,
            internal_obtained=r.internal_obtained,
            internal_max=r.internal_max,
            external_obtained=r.external_obtained,
            external_max=r.external_max,
            total_obtained=r.total_obtained,
            total_max=r.total_max,
            pass_fail=r.pass_fail,
            grade_letter=r.grade_letter,
            published_at=r.published_at,
        )
        for r in rows
    ]


async def list_result_statuses(
    scope: AccessScope, parent: User, student_user_id: str
) -> list[ParentExamResultStatusRead]:
    authorize(scope, Permission.PARENT_EXAM_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_RESULTS)
    year, semester = await _exam_term(tenant_id)
    seasons = await published_seasons(tenant_id, year=year, semester=semester)
    items: list[ParentExamResultStatusRead] = []
    for season in seasons:
        pub = await result_publication_status(tenant_id, sid, season.season_id)
        if pub is None:
            items.append(
                ParentExamResultStatusRead(
                    season_id=season.season_id,
                    status="awaiting_publication",
                    published=False,
                )
            )
        else:
            items.append(
                ParentExamResultStatusRead(
                    season_id=season.season_id,
                    status=pub.status.value,
                    published=pub.status == SemesterResultPublicationStatus.PUBLISHED,
                    published_at=pub.published_at,
                )
            )
    return items


async def hall_ticket_availability_parent(
    scope: AccessScope, parent: User, student_user_id: str, season_id: str
) -> HallTicketAvailabilityRead:
    authorize(scope, Permission.PARENT_EXAM_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_HALL_TICKET)
    ticket = await published_hall_ticket(tenant_id, sid, season_id)
    if ticket is None:
        return HallTicketAvailabilityRead(season_id=season_id, available=False)
    return HallTicketAvailabilityRead(
        season_id=season_id,
        available=True,
        ticket_number=ticket.ticket_number,
        status=ticket.status.value,
        published_at=ticket.published_at,
    )


async def download_hall_ticket_parent(
    scope: AccessScope, parent: User, student_user_id: str, season_id: str
) -> HallTicketDownloadRead:
    authorize(scope, Permission.PARENT_EXAM_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_HALL_TICKET)
    ticket = await published_hall_ticket(tenant_id, sid, season_id)
    if ticket is None:
        raise AppError(code="NOT_FOUND", message="Hall ticket not published", status_code=404)
    await ParentExamDocumentAccessHistory(
        tenant_id=tenant_id,
        parent_user_id=parent.id,
        student_user_id=sid,
        document_type="hall_ticket",
        document_ref=str(ticket.id),
    ).insert()
    from datetime import timedelta

    token = ticket.document_token or ticket.ticket_number
    expires = ticket.published_at + timedelta(days=30) if ticket.published_at else utcnow()
    return HallTicketDownloadRead(
        season_id=season_id,
        ticket_number=ticket.ticket_number,
        download_token=token,
        expires_at=expires,
    )


async def list_revaluation_status(
    scope: AccessScope, parent: User, student_user_id: str
) -> list[ParentExamReviewStatusRead]:
    authorize(scope, Permission.PARENT_EXAM_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_RESULTS)
    rows = await StudentRevaluationRequest.find({"tenant_id": tenant_id, "user_id": sid}).sort("-updated_at").to_list()
    return [
        ParentExamReviewStatusRead(
            request_id=r.request_id,
            request_type="revaluation",
            course_code=r.course_code,
            season_id=r.season_id,
            status=r.status.value,
            revised_mark_published=r.revised_mark_published,
        )
        for r in rows
    ]


async def get_academic_calendar(
    scope: AccessScope,
    parent: User,
    student_user_id: str,
) -> list[ParentExamCalendarEventRead]:
    authorize(scope, Permission.PARENT_EXAM_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_EXAM_TIMETABLE)
    year, semester = await _exam_term(tenant_id)
    events = await AcademicCalendarEvent.find({"tenant_id": tenant_id}).sort("event_at").limit(100).to_list()
    return [
        ParentExamCalendarEventRead(
            id=str(e.id),
            title=e.title,
            event_at=e.event_at,
            event_type=e.event_type,
            description=e.description,
        )
        for e in events
    ]