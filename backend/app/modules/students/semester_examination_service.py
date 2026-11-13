"""Student semester examination management (read-only)."""

from datetime import datetime, timezone

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.students.examination_portal_models import StudentExaminationNotification, StudentExaminationPreferences
from app.modules.students.examination_portal_schemas import (
    ExaminationAnnouncementRead,
    ExaminationCalendarEventRead,
    ExaminationCentreRead,
    ExaminationEligibilityRead,
    ExaminationHistoryItemRead,
    ExaminationInstructionsRead,
    ExaminationNotificationRead,
    ExaminationRegulationRead,
    ExaminationScheduleChangeRead,
    SemesterExaminationOverviewRead,
    SemesterExamSeasonRead,
    SemesterExamSessionRead,
)
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.integrations.assessment_reader import student_course_codes
from app.modules.students.integrations.semester_examination_reader import (
    centres_for_student,
    examination_history,
    published_eligibility,
    published_regulations,
    published_seasons,
    schedule_changes,
    session_by_code,
    student_announcements,
    upcoming_sessions_for_student,
)
from app.modules.students.policy import require_student_scope

_reader = StudentDataReader()


async def _term(tenant_id: PydanticObjectId) -> tuple[str, str]:
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    return context.academic_year_label, context.semester_label


async def _prefs(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> StudentExaminationPreferences:
    row = await StudentExaminationPreferences.find_one({"tenant_id": tenant_id, "user_id": user_id})
    if row is not None:
        return row
    row = StudentExaminationPreferences(tenant_id=tenant_id, user_id=user_id)
    await row.insert()
    return row


async def _primary_season(tenant_id: PydanticObjectId, year: str, semester: str) -> str | None:
    seasons = await published_seasons(tenant_id, year=year, semester=semester)
    return seasons[0].season_id if seasons else None


async def get_semester_examination_overview(scope: AccessScope, user: User) -> SemesterExaminationOverviewRead:
    authorize(scope, Permission.STUDENT_SEMESTER_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    upcoming = await upcoming_sessions_for_student(
        tenant_id, user.id, year=year, semester=semester, from_time=datetime.now(timezone.utc)
    )
    eligibility_doc = None
    season_id = await _primary_season(tenant_id, year, semester)
    if season_id:
        eligibility_doc = await published_eligibility(tenant_id, user.id, season_id)
    eligibility = (
        ExaminationEligibilityRead(
            season_id=eligibility_doc.season_id,
            status=eligibility_doc.status,
            eligible=eligibility_doc.eligible,
            reasons=eligibility_doc.reasons,
            attendance_cleared=eligibility_doc.attendance_cleared,
            fee_cleared=eligibility_doc.fee_cleared,
            published_at=eligibility_doc.published_at,
        )
        if eligibility_doc
        else None
    )
    return SemesterExaminationOverviewRead(
        academic_year_label=year,
        semester_label=semester,
        upcoming_count=len(upcoming),
        next_examination_at=upcoming[0].scheduled_start if upcoming else None,
        eligibility=eligibility,
    )


async def get_examination_calendar(scope: AccessScope, user: User) -> list[ExaminationCalendarEventRead]:
    authorize(scope, Permission.STUDENT_SEMESTER_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    sessions = await upcoming_sessions_for_student(tenant_id, user.id, year=year, semester=semester)
    events = [
        ExaminationCalendarEventRead(
            event_id=session.session_code,
            title=f"{session.course_code} examination",
            event_at=session.scheduled_start,
            event_type="semester_examination",
            course_code=session.course_code,
            metadata={"season_id": session.season_id, "room": session.room, "centre_code": session.centre_code},
        )
        for session in sessions
    ]
    academic = await _reader.academic_deadlines(tenant_id, from_time=datetime.now(timezone.utc))
    for item in academic:
        if item.event_type in {"examination", "exam", "semester_examination"}:
            events.append(
                ExaminationCalendarEventRead(
                    event_id=str(item.id),
                    title=item.title,
                    event_at=item.event_at,
                    event_type=item.event_type,
                    metadata={"description": item.description or ""},
                )
            )
    events.sort(key=lambda e: e.event_at)
    await record_audit(
        actor_id=scope.user_id,
        action="student.semester_exam.calendar_viewed",
        resource_type="student_user",
        resource_id=str(user.id),
        tenant_id=tenant_id,
    )
    return events


async def get_semester_examination_schedules(scope: AccessScope, user: User) -> list[SemesterExamSessionRead]:
    authorize(scope, Permission.STUDENT_SEMESTER_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    sessions = await upcoming_sessions_for_student(tenant_id, user.id, year=year, semester=semester)
    return [
        SemesterExamSessionRead(
            session_code=s.session_code,
            season_id=s.season_id,
            course_code=s.course_code,
            course_name=s.course_name,
            section=s.section,
            paper_code=s.paper_code,
            scheduled_start=s.scheduled_start,
            scheduled_end=s.scheduled_end,
            centre_code=s.centre_code,
            room=s.room,
            instructions=s.instructions,
        )
        for s in sessions
    ]


async def get_examination_session_details(
    scope: AccessScope, user: User, season_id: str, session_code: str
) -> SemesterExamSessionRead:
    authorize(scope, Permission.STUDENT_SEMESTER_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    session = await session_by_code(tenant_id, season_id, session_code)
    if session is None:
        raise AppError(code="NOT_FOUND", message="Examination session not found", status_code=404)
    codes = await student_course_codes(tenant_id, user.id, year=year, semester=semester)
    if session.course_code not in codes:
        raise AppError(code="FORBIDDEN", message="Examination session is not assigned to you", status_code=403)
    return SemesterExamSessionRead(
        session_code=session.session_code,
        season_id=session.season_id,
        course_code=session.course_code,
        course_name=session.course_name,
        section=session.section,
        paper_code=session.paper_code,
        scheduled_start=session.scheduled_start,
        scheduled_end=session.scheduled_end,
        centre_code=session.centre_code,
        room=session.room,
        instructions=session.instructions,
    )


async def get_examination_centres(scope: AccessScope, user: User) -> list[ExaminationCentreRead]:
    authorize(scope, Permission.STUDENT_SEMESTER_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    sessions = await upcoming_sessions_for_student(tenant_id, user.id, year=year, semester=semester)
    centre_codes = {s.centre_code for s in sessions if s.centre_code}
    centres = await centres_for_student(tenant_id, centre_codes)
    return [
        ExaminationCentreRead(
            centre_code=c.centre_code,
            name=c.name,
            building=c.building,
            address=c.address,
            contact_phone=c.contact_phone,
            room_labels=c.room_labels,
        )
        for c in centres
    ]


async def get_examination_instructions(scope: AccessScope, user: User) -> list[ExaminationInstructionsRead]:
    authorize(scope, Permission.STUDENT_SEMESTER_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    sessions = await upcoming_sessions_for_student(tenant_id, user.id, year=year, semester=semester)
    items: list[ExaminationInstructionsRead] = []
    for session in sessions:
        if not session.instructions:
            continue
        items.append(
            ExaminationInstructionsRead(
                session_code=session.session_code,
                course_code=session.course_code,
                instructions=session.instructions,
                source="semester_examination_sessions",
            )
        )
    regulations = await published_regulations(tenant_id, season_id=await _primary_season(tenant_id, year, semester))
    for reg in regulations:
        items.append(
            ExaminationInstructionsRead(
                session_code=None,
                course_code=None,
                instructions=reg.body,
                source=f"regulation:{reg.regulation_id}",
            )
        )
    return items


async def get_examination_eligibility(scope: AccessScope, user: User, season_id: str | None = None) -> ExaminationEligibilityRead:
    authorize(scope, Permission.STUDENT_SEMESTER_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    resolved_season = season_id or await _primary_season(tenant_id, year, semester)
    if resolved_season is None:
        raise AppError(code="NOT_FOUND", message="No published examination season", status_code=404)
    doc = await published_eligibility(tenant_id, user.id, resolved_season)
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Eligibility has not been published for your account", status_code=404)
    await record_audit(
        actor_id=scope.user_id,
        action="student.semester_exam.eligibility_viewed",
        resource_type="student_examination_eligibility",
        resource_id=resolved_season,
        tenant_id=tenant_id,
    )
    return ExaminationEligibilityRead(
        season_id=doc.season_id,
        status=doc.status,
        eligible=doc.eligible,
        reasons=doc.reasons,
        attendance_cleared=doc.attendance_cleared,
        fee_cleared=doc.fee_cleared,
        published_at=doc.published_at,
    )


async def get_examination_regulations(scope: AccessScope, user: User, season_id: str | None = None) -> list[ExaminationRegulationRead]:
    authorize(scope, Permission.STUDENT_SEMESTER_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    resolved = season_id or await _primary_season(tenant_id, year, semester)
    regs = await published_regulations(tenant_id, season_id=resolved)
    return [
        ExaminationRegulationRead(
            regulation_id=r.regulation_id,
            season_id=r.season_id,
            title=r.title,
            version=r.version,
            body=r.body,
            published_at=r.published_at,
        )
        for r in regs
    ]


async def get_examination_announcements(scope: AccessScope, user: User) -> list[ExaminationAnnouncementRead]:
    authorize(scope, Permission.STUDENT_SEMESTER_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    season_id = await _primary_season(tenant_id, year, semester)
    rows = await student_announcements(tenant_id, season_id=season_id)
    return [
        ExaminationAnnouncementRead(
            announcement_id=r.announcement_id,
            season_id=r.season_id,
            title=r.title,
            body=r.body,
            published_at=r.published_at,
            expires_at=r.expires_at,
        )
        for r in rows
    ]


async def get_examination_schedule_changes(scope: AccessScope, user: User) -> list[ExaminationScheduleChangeRead]:
    authorize(scope, Permission.STUDENT_SEMESTER_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    codes = await student_course_codes(tenant_id, user.id, year=year, semester=semester)
    season_id = await _primary_season(tenant_id, year, semester)
    rows = await schedule_changes(tenant_id, season_id=season_id, course_codes=codes)
    return [
        ExaminationScheduleChangeRead(
            id=str(r.id),
            season_id=r.season_id,
            session_code=r.session_code,
            course_code=r.course_code,
            change_type=r.change_type,
            summary=r.summary,
            effective_at=r.effective_at,
        )
        for r in rows
    ]


async def get_examination_history(scope: AccessScope, user: User, pagination: Pagination) -> Page[ExaminationHistoryItemRead]:
    authorize(scope, Permission.STUDENT_SEMESTER_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    rows = await examination_history(
        tenant_id,
        user.id,
        year=year,
        semester=semester,
        before=datetime.now(timezone.utc),
        limit=pagination.limit + pagination.offset,
    )
    slice_rows = rows[pagination.offset : pagination.offset + pagination.limit]
    return Page(
        items=[
            ExaminationHistoryItemRead(
                season_id=r.season_id,
                session_code=r.session_code,
                course_code=r.course_code,
                scheduled_start=r.scheduled_start,
                completed=True,
            )
            for r in slice_rows
        ],
        total=len(rows),
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_examination_notifications(scope: AccessScope, user: User, pagination: Pagination) -> Page[ExaminationNotificationRead]:
    authorize(scope, Permission.STUDENT_SEMESTER_EXAM_READ)
    tenant_id = require_student_scope(scope)
    query = StudentExaminationNotification.find({"tenant_id": tenant_id, "user_id": user.id}).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    portal_items = [
        ExaminationNotificationRead(
            id=str(r.id),
            kind=r.kind.value,
            title=r.title,
            body=r.body,
            season_id=r.season_id,
            course_code=r.course_code,
            created_at=r.created_at,
            read_at=r.read_at,
        )
        for r in rows
    ]
    if pagination.offset == 0 and not rows:
        year, semester = await _term(tenant_id)
        season_id = await _primary_season(tenant_id, year, semester)
        for ann in await student_announcements(tenant_id, season_id=season_id, limit=pagination.limit):
            portal_items.append(
                ExaminationNotificationRead(
                    id=ann.announcement_id,
                    kind="announcement",
                    title=ann.title,
                    body=ann.body,
                    season_id=ann.season_id,
                    course_code=None,
                    created_at=ann.published_at or ann.created_at,
                    read_at=None,
                )
            )
        total = len(portal_items)
    return Page(items=portal_items, total=total, limit=pagination.limit, offset=pagination.offset)


async def list_examination_seasons(scope: AccessScope, user: User) -> list[SemesterExamSeasonRead]:
    authorize(scope, Permission.STUDENT_SEMESTER_EXAM_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    seasons = await published_seasons(tenant_id, year=year, semester=semester)
    return [
        SemesterExamSeasonRead(
            season_id=s.season_id,
            title=s.title,
            academic_year_label=s.academic_year_label,
            semester_label=s.semester_label,
            starts_at=s.starts_at,
            ends_at=s.ends_at,
        )
        for s in seasons
    ]
