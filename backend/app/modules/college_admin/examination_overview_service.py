"""College admin dashboard — examination overview aggregates."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AcademicTermSummary,
    ExaminationOverviewFilters,
    ExaminationOverviewKpiRead,
    ExaminationOverviewRead,
    ExaminationPostResultItem,
    ExaminationReadinessItem,
    ExaminationResultBarItem,
    ExaminationResultsPendingItem,
    ExaminationTimetableAlert,
    ExaminationUpcomingSessionKpi,
    UpcomingExamScheduleRow,
)
from app.modules.examinations.exam_cell_enums import ExamSessionStatus
from app.modules.examinations.exam_cell_grading_enums import ExamSubjectResultOutcome
from app.modules.examinations.exam_cell_grading_models import ExamStudentSubjectResult
from app.modules.examinations.exam_cell_hall_ticket_models import ExamHallTicket
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_registration_enums import ExamHallTicketStatus, ExamRegistrationStatus
from app.modules.examinations.exam_cell_registration_models import ExamRegistration
from app.modules.examinations.exam_cell_revaluation_enums import (
    ExamRevaluationApplicationStatus,
    ExamSupplementaryRegistrationStatus,
)
from app.modules.examinations.exam_cell_revaluation_models import ExamRevaluationApplication, ExamSupplementaryRegistration
from app.modules.examinations.exam_cell_seating_enums import ExamSeatingPlanStatus
from app.modules.examinations.exam_cell_seating_models import ExamInvigilatorAssignment, ExamRoom, ExamSeatingPlan
from app.modules.examinations.exam_cell_timetable_enums import ExamScheduleApprovalDecision, ExamTimetableEntryStatus, ExamTimetableStatus
from app.modules.examinations.exam_cell_timetable_models import ExamScheduleApproval, ExamTimetable, ExamTimetableEntry
from app.modules.examinations.examination_registration_enums import SemesterResultPublicationStatus
from app.modules.examinations.result_publication_models import SemesterResultPublication
from app.modules.students.models import StudentProfile

_reader = OperationalDataReader()
_IST = ZoneInfo("Asia/Kolkata")

_ACTIVE_EXAM_STATUSES = frozenset(
    {
        ExamSessionStatus.SCHEDULED,
        ExamSessionStatus.REGISTRATION_OPEN,
        ExamSessionStatus.REGISTRATION_CLOSED,
        ExamSessionStatus.ONGOING,
        ExamSessionStatus.COMPLETED,
        ExamSessionStatus.RESULTS_PROCESSING,
    }
)

_RESULT_BAR_BUCKETS: tuple[tuple[str, str], ...] = (
    ("be_y1", "B.E. Yr 1"),
    ("be_y2", "B.E. Yr 2"),
    ("be_y3", "B.E. Yr 3"),
    ("be_y4", "B.E. Yr 4"),
    ("me", "M.E."),
    ("mba", "MBA"),
    ("mca", "MCA"),
)


def _batch_start_year(batch_label: str | None) -> int | None:
    if not batch_label:
        return None
    match = re.match(r"^(\d{4})", batch_label.strip())
    return int(match.group(1)) if match else None


def _academic_year_start(academic_year_label: str | None) -> int | None:
    if not academic_year_label:
        return None
    match = re.match(r"^(\d{4})", academic_year_label.strip())
    return int(match.group(1)) if match else None


def _study_year(batch_label: str | None, academic_year_label: str | None) -> int | None:
    batch_start = _batch_start_year(batch_label)
    ay_start = _academic_year_start(academic_year_label)
    if batch_start is None or ay_start is None:
        return None
    return max(1, min(6, ay_start - batch_start + 1))


def _programme_level(prog: AcademicProgramme | None) -> str:
    if prog is None:
        return "undergraduate"
    if prog.duration_semesters <= 4 and prog.credits_required <= 80:
        return "doctoral"
    if prog.duration_semesters <= 6:
        return "postgraduate"
    return "undergraduate"


def _result_bucket(programme_code: str | None, batch_label: str | None, ay_label: str | None, prog: AcademicProgramme | None) -> str | None:
    code = (programme_code or "").upper()
    level = _programme_level(prog)
    if "MBA" in code:
        return "mba"
    if "MCA" in code:
        return "mca"
    if level in ("postgraduate", "doctoral") or code.startswith("M") or "M.TECH" in code or "M.E" in code:
        return "me"
    year = _study_year(batch_label, ay_label)
    if year is None:
        return None
    return f"be_y{min(year, 4)}"


def _fmt_ist(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_IST)


def _session_date_label(dt: datetime) -> str:
    local = _fmt_ist(dt)
    return f"{local.day} {local.strftime('%b')}"


def _session_time_label(dt: datetime, session_label: str | None) -> str:
    local = _fmt_ist(dt)
    shift = session_label or "FN"
    return f"{shift} ({local.strftime('%H:%M')})"


def _pick_focus_session(sessions: list[ExamSession], *, now: datetime) -> ExamSession | None:
    if not sessions:
        return None
    reference = as_utc_aware(now)
    active = [s for s in sessions if s.status in _ACTIVE_EXAM_STATUSES]
    if not active:
        active = sessions
    upcoming = [
        s
        for s in active
        if s.examination_start_at and as_utc_aware(s.examination_start_at) >= reference
    ]
    if upcoming:
        return min(upcoming, key=lambda s: as_utc_aware(s.examination_start_at))
    ongoing = [
        s
        for s in active
        if s.examination_start_at
        and s.examination_end_at
        and as_utc_aware(s.examination_start_at) <= reference <= as_utc_aware(s.examination_end_at)
    ]
    if ongoing:
        return ongoing[0]
    return max(active, key=lambda s: s.examination_start_at or s.created_at)


def _row_status(entries: list[ExamTimetableEntry], *, session_invigilators: int) -> tuple[str, str]:
    missing_room = any(not (e.room_label or e.facility_id) for e in entries)
    if missing_room:
        return "seating_pending", "Seating pending"
    if session_invigilators <= 0:
        return "invigilators_due", "Invigilators due"
    return "ready", "Ready"


async def get_examination_overview(
    scope: AccessScope,
    *,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    exam_session_id: str | None = None,
) -> ExaminationOverviewRead:
    authorize(scope, Permission.COLLEGE_DASHBOARD_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    year, semester = await _reader.current_academic_term(tenant_id)
    ay_label = academic_year_label or year
    sem_label = semester_label or semester

    sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).to_list()
    if ay_label:
        sessions = [s for s in sessions if s.academic_year_label == ay_label]
    if sem_label:
        sessions = [s for s in sessions if s.semester_label == sem_label]

    focus: ExamSession | None = None
    if exam_session_id:
        oid = PydanticObjectId(exam_session_id) if exam_session_id else None
        focus = next((s for s in sessions if s.id == oid), None)
    focus = focus or _pick_focus_session(sessions, now=now)

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    prog_by_code = {(p.code or "").upper(): p for p in programmes}

    timetable_alert: ExaminationTimetableAlert | None = None
    timetables = await ExamTimetable.find(Eq(ExamTimetable.tenant_id, tenant_id)).to_list()
    if focus:
        timetables = [t for t in timetables if t.exam_session_id == focus.id]
    pending_tt = next(
        (t for t in timetables if t.status in (ExamTimetableStatus.IN_REVIEW, ExamTimetableStatus.DRAFT)),
        None,
    )
    if pending_tt is None:
        for tt in timetables:
            pending_approval = await ExamScheduleApproval.find_one(
                Eq(ExamScheduleApproval.tenant_id, tenant_id),
                Eq(ExamScheduleApproval.timetable_id, tt.id),
                Eq(ExamScheduleApproval.decision, ExamScheduleApprovalDecision.PENDING),
            )
            if pending_approval:
                pending_tt = tt
                break
    if pending_tt:
        submitted = pending_tt.updated_at or pending_tt.created_at
        timetable_alert = ExaminationTimetableAlert(
            title="Exam timetable awaiting College Admin approval",
            description=(
                f"{pending_tt.title} submitted for approval. "
                "Approval is required before hall tickets can be published."
            ),
            submitted_at=submitted,
            timetable_id=pending_tt.timetable_id,
            review_href_note="Review timetable",
        )

    papers_total = 0
    papers_received = 0
    programme_codes: set[str] = set()
    upcoming_rows: list[UpcomingExamScheduleRow] = []
    upcoming_total = 0
    result_bars: list[ExaminationResultBarItem] = []

    upcoming_session_kpi = ExaminationUpcomingSessionKpi()
    hall_issued = 0
    hall_withheld = 0
    hall_total = 0

    if focus:
        local_start = _fmt_ist(focus.examination_start_at) if focus.examination_start_at else None
        local_end = _fmt_ist(focus.examination_end_at) if focus.examination_end_at else None
        days_to_go = None
        if focus.examination_start_at:
            delta = (_fmt_ist(focus.examination_start_at).date() - now.astimezone(_IST).date()).days
            days_to_go = max(0, delta)
        upcoming_session_kpi = ExaminationUpcomingSessionKpi(
            session_name=focus.name,
            session_code=focus.session_code,
            date_range_label=(
                f"{local_start.day}–{local_end.day} {local_end.strftime('%b %Y')}"
                if local_start and local_end
                else None
            ),
            days_to_go=days_to_go,
            exam_session_id=str(focus.id),
        )

        entries = await ExamTimetableEntry.find(
            Eq(ExamTimetableEntry.tenant_id, tenant_id),
            Eq(ExamTimetableEntry.status, ExamTimetableEntryStatus.ACTIVE),
        ).to_list()
        tt_ids = {t.id for t in timetables}
        if tt_ids:
            entries = [e for e in entries if e.timetable_id in tt_ids]
        papers_total = len(entries)
        programme_codes = {e.programme_code for e in entries if e.programme_code}
        papers_received = sum(
            1
            for e in entries
            if bool(e.metadata.get("question_paper_received"))
            or (e.paper_code and (e.room_label or e.centre_code))
        )

        session_invigilators = await ExamInvigilatorAssignment.find(
            Eq(ExamInvigilatorAssignment.tenant_id, tenant_id),
            Eq(ExamInvigilatorAssignment.exam_session_id, focus.id),
            Eq(ExamInvigilatorAssignment.active, True),
        ).count()

        groups: dict[str, list[ExamTimetableEntry]] = defaultdict(list)
        for entry in entries:
            if entry.scheduled_start < now:
                continue
            day_key = _fmt_ist(entry.scheduled_start).date().isoformat()
            slot = entry.session_label or entry.shift_label or "FN"
            prog = entry.student_group_label or entry.programme_code or "All programmes"
            key = f"{day_key}|{slot}|{prog}"
            groups[key].append(entry)

        candidate_ids: set[PydanticObjectId] = set()
        reg_statuses = (
            ExamRegistrationStatus.SUBMITTED,
            ExamRegistrationStatus.CONFIRMED,
        )
        regs = await ExamRegistration.find(
            Eq(ExamRegistration.tenant_id, tenant_id),
            Eq(ExamRegistration.exam_session_id, focus.id),
            In(ExamRegistration.status, [s.value for s in reg_statuses]),
        ).to_list()
        candidate_ids = {r.student_user_id for r in regs}

        rooms = await ExamRoom.find(
            Eq(ExamRoom.tenant_id, tenant_id),
            Eq(ExamRoom.exam_session_id, focus.id),
            Eq(ExamRoom.active, True),
        ).to_list()
        for key in sorted(groups.keys()):
            group_entries = groups[key]
            first = min(group_entries, key=lambda e: e.scheduled_start)
            date_session = f"{_session_date_label(first.scheduled_start)} · {_session_time_label(first.scheduled_start, first.session_label)}"
            programme_label = first.student_group_label or first.programme_code or "—"
            if first.programme_code and first.programme_code.upper() in prog_by_code:
                programme_label = prog_by_code[first.programme_code.upper()].name
            halls_in_group = {e.room_label for e in group_entries if e.room_label}
            status_key, status_label = _row_status(group_entries, session_invigilators=session_invigilators)
            upcoming_rows.append(
                UpcomingExamScheduleRow(
                    row_key=key,
                    date_session_label=date_session,
                    programme_label=programme_label,
                    papers_count=len(group_entries),
                    candidates_count=len(candidate_ids) if candidate_ids else None,
                    halls_count=len(halls_in_group) or None,
                    status_key=status_key,
                    status_label=status_label,
                )
            )
        upcoming_rows.sort(key=lambda r: r.date_session_label)
        upcoming_total = len(upcoming_rows)
        upcoming_rows = upcoming_rows[:5]

        tickets = await ExamHallTicket.find(
            Eq(ExamHallTicket.tenant_id, tenant_id),
            Eq(ExamHallTicket.exam_session_id, focus.id),
        ).to_list()
        hall_issued = sum(1 for t in tickets if t.status == ExamHallTicketStatus.PUBLISHED)
        hall_withheld = sum(
            1
            for t in tickets
            if t.status in (ExamHallTicketStatus.DRAFT, ExamHallTicketStatus.GENERATED, ExamHallTicketStatus.REVOKED)
        )
        confirmed_regs = [r for r in regs if r.status == ExamRegistrationStatus.CONFIRMED]
        hall_total = len(confirmed_regs) if confirmed_regs else len(regs) or len(tickets)
        fee_withheld = sum(1 for r in regs if not r.fee_verified and r.status != ExamRegistrationStatus.CANCELLED)
        hall_withheld = max(hall_withheld, fee_withheld)

        session_results = await ExamStudentSubjectResult.find(
            Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
            Eq(ExamStudentSubjectResult.exam_session_id, focus.id),
        ).to_list()
        profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
        profile_by_user = {p.user_id: p for p in profiles}
        bucket_stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for row in session_results:
            profile = profile_by_user.get(row.student_user_id)
            bucket = _result_bucket(
                profile.programme_code if profile else None,
                profile.batch_label if profile else None,
                ay_label,
                prog_by_code.get((profile.programme_code or "").upper()) if profile else None,
            )
            if bucket is None:
                continue
            if row.outcome == ExamSubjectResultOutcome.PASS:
                bucket_stats[bucket][0] += 1
            else:
                bucket_stats[bucket][1] += 1
        for key, label in _RESULT_BAR_BUCKETS:
            passed, failed = bucket_stats.get(key, [0, 0])
            total = passed + failed
            if total == 0:
                continue
            result_bars.append(
                ExaminationResultBarItem(
                    bucket_key=key,
                    label=label,
                    pass_rate_pct=round((passed / total) * 100, 1),
                    student_count=total,
                )
            )

    results_pending: list[ExaminationResultsPendingItem] = []
    for session in sessions:
        if session.status == ExamSessionStatus.RESULTS_PROCESSING:
            results_pending.append(
                ExaminationResultsPendingItem(
                    exam_session_id=str(session.id),
                    label=f"{session.semester_label} {session.examination_type.value}",
                    session_name=session.name,
                )
            )
    processing_pub_count = await SemesterResultPublication.find(
        Eq(SemesterResultPublication.tenant_id, tenant_id),
        Eq(SemesterResultPublication.status, SemesterResultPublicationStatus.PROCESSING),
    ).count()
    if processing_pub_count and not results_pending:
        results_pending.append(
            ExaminationResultsPendingItem(
                exam_session_id=str(focus.id) if focus else "",
                label=f"{sem_label or 'Semester'} results processing",
                session_name="Result publication queue",
            )
        )

    issued_pct = round((hall_issued / hall_total) * 100, 1) if hall_total else None

    kpis = ExaminationOverviewKpiRead(
        upcoming_session=upcoming_session_kpi,
        papers_scheduled=papers_total,
        programmes_count=len(programme_codes) or len(prog_by_code),
        hall_tickets_issued=hall_issued,
        hall_tickets_total=hall_total,
        hall_tickets_issued_pct=issued_pct,
        hall_tickets_withheld=hall_withheld,
        results_pending_count=len(results_pending) or processing_pub_count,
        results_pending=results_pending[:5],
    )

    readiness: list[ExaminationReadinessItem] = []
    if focus:
        reg_closed = focus.status in (
            ExamSessionStatus.REGISTRATION_CLOSED,
            ExamSessionStatus.ONGOING,
            ExamSessionStatus.COMPLETED,
            ExamSessionStatus.RESULTS_PROCESSING,
            ExamSessionStatus.PUBLISHED,
        ) or (focus.registration_end_at and focus.registration_end_at <= now)
        reg_count = await ExamRegistration.find(
            Eq(ExamRegistration.tenant_id, tenant_id),
            Eq(ExamRegistration.exam_session_id, focus.id),
            In(
                ExamRegistration.status,
                [ExamRegistrationStatus.CONFIRMED.value, ExamRegistrationStatus.SUBMITTED.value],
            ),
        ).count()
        readiness.append(
            ExaminationReadinessItem(
                step_key="registration_closed",
                label="Exam registration closed",
                description=f"{reg_count:,} students registered",
                status_key="done" if reg_closed else "pending",
                status_label="Done" if reg_closed else "Pending",
            )
        )
        papers_complete = papers_total > 0 and papers_received >= papers_total
        readiness.append(
            ExaminationReadinessItem(
                step_key="question_papers",
                label="Question papers received",
                description=f"{papers_received:,} of {papers_total:,} sealed" if papers_total else "No papers scheduled yet",
                status_key="done" if papers_complete else ("pending" if papers_total else "not_started"),
                status_label="Done" if papers_complete else ("Pending" if papers_total else "Not started"),
            )
        )
        tt_pending = pending_tt is not None
        readiness.append(
            ExaminationReadinessItem(
                step_key="timetable_approval",
                label="Timetable approval",
                description="Awaiting College Admin" if tt_pending else "Approved for publication",
                status_key="pending" if tt_pending else "done",
                status_label="Pending" if tt_pending else "Done",
            )
        )
        rooms = await ExamRoom.find(Eq(ExamRoom.tenant_id, tenant_id), Eq(ExamRoom.exam_session_id, focus.id)).to_list() if focus else []
        active_rooms = [r for r in rooms if r.active]
        plans = await ExamSeatingPlan.find(
            Eq(ExamSeatingPlan.tenant_id, tenant_id),
            Eq(ExamSeatingPlan.exam_session_id, focus.id),
        ).to_list()
        seating_pct = round((len(plans) / max(len(active_rooms), 1)) * 100) if active_rooms else None
        readiness.append(
            ExaminationReadinessItem(
                step_key="seating_allocation",
                label="Hall & seating allocation",
                description=(
                    f"{len(plans)} of {len(active_rooms)} halls allocated"
                    if active_rooms
                    else "No exam halls configured"
                ),
                status_key="in_progress" if seating_pct and seating_pct < 100 else ("done" if plans else "not_started"),
                status_label=f"{seating_pct:.0f}%" if seating_pct is not None and seating_pct < 100 else ("Done" if plans else "Not started"),
                progress_pct=seating_pct,
            )
        )
        inv_count = await ExamInvigilatorAssignment.find(
            Eq(ExamInvigilatorAssignment.tenant_id, tenant_id),
            Eq(ExamInvigilatorAssignment.exam_session_id, focus.id),
            Eq(ExamInvigilatorAssignment.active, True),
        ).count()
        inv_started = inv_count > 0
        readiness.append(
            ExaminationReadinessItem(
                step_key="invigilator_allocation",
                label="Invigilator allocation",
                description="Duty rosters published" if inv_started else "Starts after seating",
                status_key="done" if inv_started else "not_started",
                status_label="Done" if inv_started else "Not started",
            )
        )

    reval_apps = await ExamRevaluationApplication.find(Eq(ExamRevaluationApplication.tenant_id, tenant_id)).to_list()
    if focus:
        reval_apps = [a for a in reval_apps if a.exam_session_id == focus.id]
    reval_open = sum(
        1
        for a in reval_apps
        if a.status
        not in (
            ExamRevaluationApplicationStatus.APPROVED,
            ExamRevaluationApplicationStatus.REJECTED,
            ExamRevaluationApplicationStatus.WITHDRAWN,
        )
    )
    reval_done = sum(1 for a in reval_apps if a.status == ExamRevaluationApplicationStatus.APPROVED)
    grade_changes = reval_done

    supp_regs = await ExamSupplementaryRegistration.find(Eq(ExamSupplementaryRegistration.tenant_id, tenant_id)).to_list()
    if focus:
        supp_regs = [
            s
            for s in supp_regs
            if s.exam_session_id == focus.id or s.supplementary_season_id == focus.season_id
        ]
    supp_confirmed = sum(1 for s in supp_regs if s.status == ExamSupplementaryRegistrationStatus.CONFIRMED)

    result_title = None
    if focus:
        result_title = f"{focus.semester_label} semester {focus.academic_year_label.split('-')[0] if focus.academic_year_label else ''}".strip()

    post_result = [
        ExaminationPostResultItem(
            item_key="revaluation_requests",
            label="Revaluation requests",
            description=result_title,
            count=reval_open + reval_done if reval_apps else 0,
        ),
        ExaminationPostResultItem(
            item_key="revaluation_completed",
            label="Completed revaluations",
            description=f"{grade_changes} grade changes" if grade_changes else "No grade changes yet",
            count=reval_done,
        ),
        ExaminationPostResultItem(
            item_key="supplementary",
            label="Supplementary registrations",
            description=focus.name if focus and focus.examination_type.value == "supplementary" else "Current cycle",
            count=supp_confirmed or len(supp_regs),
        ),
    ]

    return ExaminationOverviewRead(
        filters=ExaminationOverviewFilters(
            academic_year_label=ay_label,
            semester_label=sem_label,
            exam_session_id=str(focus.id) if focus else exam_session_id,
        ),
        academic_term=AcademicTermSummary(academic_year_label=ay_label, semester_label=sem_label),
        kpis=kpis,
        timetable_alert=timetable_alert,
        upcoming_schedule=upcoming_rows,
        upcoming_schedule_total=upcoming_total,
        upcoming_schedule_limit=5,
        result_summary_title=result_title,
        result_summary_bars=result_bars,
        readiness_checklist=readiness,
        post_result_activity=post_result,
        generated_at=utcnow(),
    )