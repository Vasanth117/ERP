"""Examination administration overview dashboard (CA 09.01)."""

from __future__ import annotations

import math
from datetime import timedelta
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.modules.college_admin.examination_overview_service import _pick_focus_session
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    ExaminationDashboardPageRead,
    ExaminationDashboardSessionRow,
    FacultyAssignmentWorkflowStep,
    PoliciesPagination,
    StudentAdminWorkQueueItem,
    UserDashboardKpi,
)
from app.modules.college_admin.student_administration_dashboard_page_service import _fmt_time_label
from app.modules.examinations.exam_cell_assessment_enums import ExamAssessmentConfigStatus
from app.modules.examinations.exam_cell_assessment_models import ExamAssessmentConfig
from app.modules.examinations.exam_cell_enums import ExamSessionStatus, ExamSessionType
from app.modules.examinations.exam_cell_hall_ticket_models import ExamHallTicket
from app.modules.examinations.exam_cell_marks_enums import ExamMarksSubmissionStatus
from app.modules.examinations.exam_cell_marks_models import ExamMarksSubmission
from app.modules.examinations.exam_cell_models import ExamSession, ExamSessionAcademicScope
from app.modules.examinations.exam_cell_registration_enums import ExamHallTicketStatus, ExamRegistrationStatus
from app.modules.examinations.exam_cell_registration_models import ExamEligibilityRecord, ExamRegistration
from app.modules.examinations.exam_cell_seating_models import ExamInvigilatorAssignment, ExamRoom, ExamSeatingPlan
from app.modules.examinations.exam_cell_timetable_enums import ExamTimetableStatus
from app.modules.examinations.exam_cell_timetable_models import ExamTimetable, ExamTimetableEntry
from app.modules.examinations.enums import MarksBatchStatus
from app.modules.examinations.models import MarksSubmissionBatch

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 8

_TYPE_LABELS: dict[ExamSessionType, str] = {
    ExamSessionType.REGULAR: "Regular",
    ExamSessionType.ARREAR: "Arrear",
    ExamSessionType.SUPPLEMENTARY: "Supplementary",
    ExamSessionType.SPECIAL: "Internal",
}

_SESSION_STATUS: dict[ExamSessionStatus, tuple[str, str]] = {
    ExamSessionStatus.DRAFT: ("Draft", "muted"),
    ExamSessionStatus.SCHEDULED: ("Scheduled", "info"),
    ExamSessionStatus.REGISTRATION_OPEN: ("Scheduled", "info"),
    ExamSessionStatus.REGISTRATION_CLOSED: ("Scheduled", "info"),
    ExamSessionStatus.ONGOING: ("Ongoing", "warning"),
    ExamSessionStatus.COMPLETED: ("Completed", "success"),
    ExamSessionStatus.RESULTS_PROCESSING: ("Processing", "warning"),
    ExamSessionStatus.PUBLISHED: ("Completed", "success"),
    ExamSessionStatus.ARCHIVED: ("Archived", "muted"),
    ExamSessionStatus.CANCELLED: ("Cancelled", "error"),
}

_WORKFLOW_DEF: list[tuple[str, str, int, str]] = [
    ("create_examination", "Create examination", 1, "/college-admin/examinations/examination-session-management"),
    ("configure_subjects", "Configure subjects", 2, "/college-admin/examinations/examination-configuration"),
    ("generate_timetable", "Generate timetable", 3, "/college-admin/examinations/exam-timetable-management"),
    ("assign_halls", "Assign halls", 4, "/college-admin/examinations/examination-hall-seating-management"),
    ("marks_entry", "Marks entry", 5, "/college-admin/examinations/marks-entry-management"),
    (
        "result_approval",
        "Result approval and publication",
        6,
        "/college-admin/examinations/result-approval",
    ),
]


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _period_label(session: ExamSession) -> str:
    start = as_utc_aware(session.examination_start_at).astimezone(_IST) if session.examination_start_at else None
    end = as_utc_aware(session.examination_end_at).astimezone(_IST) if session.examination_end_at else None
    if start and end:
        if start.month == end.month and start.year == end.year:
            return f"{start.day}–{end.day} {end.strftime('%b %Y')}"
        return f"{start.strftime('%d %b')}–{end.strftime('%d %b %Y')}"
    if start:
        return start.strftime("%d %b %Y")
    return "—"


def _focus_subtitle(session: ExamSession | None) -> str:
    if not session:
        return "Exam sessions, registration, halls, marks and results"
    start = as_utc_aware(session.examination_start_at).astimezone(_IST) if session.examination_start_at else None
    starts = f"Starts {start.strftime('%d %b %Y')}" if start else "Schedule pending"
    return f"{session.name or session.session_code} · {starts}"


async def _workflow_active_key(tenant_id: PydanticObjectId, focus: ExamSession | None, *, has_sessions: bool) -> str:
    if not has_sessions or focus is None:
        return "create_examination"
    assessment = await ExamAssessmentConfig.find_one(
        {
            "tenant_id": tenant_id,
            "academic_year_label": focus.academic_year_label,
            "semester_label": focus.semester_label,
            "status": ExamAssessmentConfigStatus.ACTIVE.value,
        }
    )
    if assessment is None:
        return "configure_subjects"
    timetable = await ExamTimetable.find_one(
        Eq(ExamTimetable.tenant_id, tenant_id),
        Eq(ExamTimetable.exam_session_id, focus.id),
    )
    if timetable is None or timetable.status != ExamTimetableStatus.PUBLISHED:
        return "generate_timetable"
    rooms = await ExamRoom.find(
        Eq(ExamRoom.tenant_id, tenant_id),
        Eq(ExamRoom.exam_session_id, focus.id),
        Eq(ExamRoom.active, True),
    ).count()
    plans = await ExamSeatingPlan.find(
        Eq(ExamSeatingPlan.tenant_id, tenant_id),
        Eq(ExamSeatingPlan.exam_session_id, focus.id),
    ).count()
    if rooms > 0 and plans < rooms:
        return "assign_halls"
    total_submissions = await ExamMarksSubmission.find(
        Eq(ExamMarksSubmission.tenant_id, tenant_id),
        Eq(ExamMarksSubmission.exam_session_id, focus.id),
    ).count()
    approved = await ExamMarksSubmission.find(
        {
            "tenant_id": tenant_id,
            "exam_session_id": focus.id,
            "status": {
                "$in": [ExamMarksSubmissionStatus.APPROVED.value, ExamMarksSubmissionStatus.LOCKED.value],
            },
        }
    ).count()
    if total_submissions == 0 or approved < total_submissions:
        return "marks_entry"
    if focus.status not in (ExamSessionStatus.PUBLISHED, ExamSessionStatus.COMPLETED):
        return "result_approval"
    return "result_approval"


def _workflow_steps(active_key: str) -> list[FacultyAssignmentWorkflowStep]:
    active_index = next((i for i, (key, *_) in enumerate(_WORKFLOW_DEF) if key == active_key), 0)
    steps: list[FacultyAssignmentWorkflowStep] = []
    for index, (key, label, number, href) in enumerate(_WORKFLOW_DEF):
        if index < active_index:
            status = "done"
        elif index == active_index:
            status = "active"
        else:
            status = "pending"
        steps.append(FacultyAssignmentWorkflowStep(key=key, label=label, step_number=number, status=status, href=href))
    return steps


async def _programmes_label(tenant_id: PydanticObjectId, session_id: PydanticObjectId) -> str:
    scope = await ExamSessionAcademicScope.find_one(
        Eq(ExamSessionAcademicScope.tenant_id, tenant_id),
        Eq(ExamSessionAcademicScope.exam_session_id, session_id),
    )
    if scope is None or not scope.programme_codes:
        return "All"
    if len(scope.programme_codes) == 1:
        return scope.programme_codes[0]
    return f"{len(scope.programme_codes)} programmes"


async def get_examination_dashboard_page(
    scope: AccessScope,
    *,
    page: int = 1,
) -> ExaminationDashboardPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).sort("-examination_start_at").to_list()
    focus = _pick_focus_session(sessions, now=now)
    active_key = await _workflow_active_key(tenant_id, focus, has_sessions=bool(sessions))

    reg_statuses = [ExamRegistrationStatus.SUBMITTED.value, ExamRegistrationStatus.CONFIRMED.value]
    registered_total = 0
    hall_generated = 0
    not_eligible = 0
    papers_overdue = 0

    if focus:
        registered_total = await ExamRegistration.find(
            Eq(ExamRegistration.tenant_id, tenant_id),
            Eq(ExamRegistration.exam_session_id, focus.id),
            In(ExamRegistration.status, reg_statuses),
        ).count()
        hall_generated = await ExamHallTicket.find(
            Eq(ExamHallTicket.tenant_id, tenant_id),
            Eq(ExamHallTicket.exam_session_id, focus.id),
            In(
                ExamHallTicket.status,
                [ExamHallTicketStatus.GENERATED.value, ExamHallTicketStatus.PUBLISHED.value],
            ),
        ).count()
        not_eligible = await ExamEligibilityRecord.find(
            Eq(ExamEligibilityRecord.tenant_id, tenant_id),
            Eq(ExamEligibilityRecord.exam_session_id, focus.id),
            Eq(ExamEligibilityRecord.overall_eligible, False),
        ).count()
        cutoff = now - timedelta(days=14)
        papers_overdue = await ExamMarksSubmission.find(
            {
                "tenant_id": tenant_id,
                "exam_session_id": focus.id,
                "status": {"$nin": [ExamMarksSubmissionStatus.APPROVED.value, ExamMarksSubmissionStatus.LOCKED.value]},
                "created_at": {"$lte": cutoff},
            }
        ).count()
        legacy_overdue = await MarksSubmissionBatch.find(
            {
                "tenant_id": tenant_id,
                "status": {"$in": [MarksBatchStatus.DRAFT.value, MarksBatchStatus.SUBMITTED.value]},
                "created_at": {"$lte": cutoff},
            }
        ).count()
        papers_overdue += legacy_overdue
    else:
        registered_total = await ExamRegistration.find(
            Eq(ExamRegistration.tenant_id, tenant_id),
            In(ExamRegistration.status, reg_statuses),
        ).count()
        hall_generated = await ExamHallTicket.find(
            Eq(ExamHallTicket.tenant_id, tenant_id),
            In(
                ExamHallTicket.status,
                [ExamHallTicketStatus.GENERATED.value, ExamHallTicketStatus.PUBLISHED.value],
            ),
        ).count()
        not_eligible = await ExamEligibilityRecord.find(
            Eq(ExamEligibilityRecord.tenant_id, tenant_id),
            Eq(ExamEligibilityRecord.overall_eligible, False),
        ).count()
        cutoff = now - timedelta(days=14)
        papers_overdue = await ExamMarksSubmission.find(
            {
                "tenant_id": tenant_id,
                "status": {"$nin": [ExamMarksSubmissionStatus.APPROVED.value, ExamMarksSubmissionStatus.LOCKED.value]},
                "created_at": {"$lte": cutoff},
            }
        ).count()

    hall_unassigned = 0
    invigilator_gaps = 0
    eligibility_review = 0
    if focus:
        rooms = await ExamRoom.find(
            Eq(ExamRoom.tenant_id, tenant_id),
            Eq(ExamRoom.exam_session_id, focus.id),
            Eq(ExamRoom.active, True),
        ).to_list()
        plans = await ExamSeatingPlan.find(
            Eq(ExamSeatingPlan.tenant_id, tenant_id),
            Eq(ExamSeatingPlan.exam_session_id, focus.id),
        ).count()
        hall_unassigned = max(0, len(rooms) - plans) if rooms else 0
        invigilator_count = await ExamInvigilatorAssignment.find(
            Eq(ExamInvigilatorAssignment.tenant_id, tenant_id),
            Eq(ExamInvigilatorAssignment.exam_session_id, focus.id),
            Eq(ExamInvigilatorAssignment.active, True),
        ).count()
        tt_entries = await ExamTimetableEntry.find(
            Eq(ExamTimetableEntry.tenant_id, tenant_id),
        ).to_list()
        timetables = await ExamTimetable.find(
            Eq(ExamTimetable.tenant_id, tenant_id),
            Eq(ExamTimetable.exam_session_id, focus.id),
        ).to_list()
        tt_ids = {t.id for t in timetables}
        session_entries = [e for e in tt_entries if e.timetable_id in tt_ids]
        invigilator_gaps = max(0, len(session_entries) - invigilator_count) if session_entries else 0
        eligibility_review = await ExamEligibilityRecord.find(
            Eq(ExamEligibilityRecord.tenant_id, tenant_id),
            Eq(ExamEligibilityRecord.exam_session_id, focus.id),
            Eq(ExamEligibilityRecord.published, False),
        ).count()
    else:
        eligibility_review = await ExamEligibilityRecord.find(
            Eq(ExamEligibilityRecord.tenant_id, tenant_id),
            Eq(ExamEligibilityRecord.published, False),
        ).count()

    total = len(sessions)
    total_pages = math.ceil(total / _PAGE_SIZE) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_sessions = sessions[start : start + _PAGE_SIZE]

    session_rows: list[ExaminationDashboardSessionRow] = []
    for session in page_sessions:
        students = await ExamRegistration.find(
            Eq(ExamRegistration.tenant_id, tenant_id),
            Eq(ExamRegistration.exam_session_id, session.id),
            In(ExamRegistration.status, reg_statuses),
        ).count()
        status_label, status_tone = _SESSION_STATUS.get(session.status, ("—", "muted"))
        session_rows.append(
            ExaminationDashboardSessionRow(
                session_id=session.session_id,
                session_label=session.name or session.session_code,
                type_label=_TYPE_LABELS.get(session.examination_type, session.examination_type.value.title()),
                period_label=_period_label(session),
                programmes_label=await _programmes_label(tenant_id, session.id),
                students_count=students,
                status_label=status_label,
                status_tone=status_tone,
                detail_href="/college-admin/examinations/examination-session-management",
            )
        )

    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)

    unassigned_label = "Unassigned halls" if hall_unassigned != 1 else "Unassigned hall"
    pending_items = [
        StudentAdminWorkQueueItem(
            key="hall_allocation",
            title="Hall allocation",
            subtitle=unassigned_label,
            count=hall_unassigned,
            href="/college-admin/examinations/examination-hall-seating-management",
            action_label="Open →",
            icon_slug="building",
        ),
        StudentAdminWorkQueueItem(
            key="invigilation_gaps",
            title="Invigilation gaps",
            subtitle="Sessions",
            count=invigilator_gaps,
            href="/college-admin/examinations/invigilator-allocation",
            action_label="Open →",
            icon_slug="users",
        ),
        StudentAdminWorkQueueItem(
            key="eligibility_review",
            title="Eligibility review",
            subtitle="Students",
            count=eligibility_review,
            href="/college-admin/examinations/student-exam-eligibility",
            action_label="Open →",
            icon_slug="clipboard-list",
        ),
    ]

    kpis = [
        UserDashboardKpi(
            key="registered",
            label="Registered",
            value=f"{registered_total:,}",
            hint_line="Students",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="hall_tickets",
            label="Hall tickets",
            value=f"{hall_generated:,}",
            hint_line="Generated",
            hint_tone="success",
        ),
        UserDashboardKpi(
            key="not_eligible",
            label="Not eligible",
            value=f"{not_eligible:,}",
            hint_line="Attendance or dues",
            hint_tone="error" if not_eligible else "success",
        ),
        UserDashboardKpi(
            key="papers_overdue",
            label="Papers",
            value=f"{papers_overdue:,}",
            hint_line="Over 14 days",
            hint_tone="warning" if papers_overdue else "success",
        ),
    ]

    return ExaminationDashboardPageRead(
        page_title="Examination Dashboard",
        page_subtitle=_focus_subtitle(focus),
        export_label="Export",
        create_examination_label="Create examination",
        create_examination_href="/college-admin/examinations/examination-session-management",
        scope_indicator_label="College scope",
        updated_at_label=_fmt_time_label(now),
        workflow_steps=_workflow_steps(active_key),
        kpis=kpis,
        sessions_section_title="Examination sessions",
        sessions_count_label=f"{total:,} sessions" if total else "0 sessions",
        table_headers=["Session", "Type", "Period", "Programmes", "Students", "Status"],
        session_rows=session_rows,
        showing_label=f"Showing {showing_from}–{showing_to} of {total:,}" if total else "Showing 0 of 0",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1 and bool(total),
            has_next=page < total_pages,
        ),
        pending_title="Pending",
        pending_items=pending_items,
        footer_disclaimer="Live institutional data · Examinations, halls and results · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )