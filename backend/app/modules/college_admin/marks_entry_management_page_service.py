"""Marks entry management page (CA 09.08)."""

from __future__ import annotations

import math
from collections import defaultdict
from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.exam_registration_management_page_service import _select_session
from app.modules.college_admin.examination_workflow import empty_state_for_step, workflow_chrome
from app.modules.college_admin.examination_marks_assessment_nav import examination_marks_assessment_sub_nav
from app.modules.college_admin.examination_overview_service import _pick_focus_session
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    MarksEntryManagementActionPayload,
    MarksEntryManagementPageRead,
    MarksEntryManagementProgressRow,
    PoliciesPagination,
)
from app.modules.examinations.exam_cell_audit import record_exam_activity
from app.modules.examinations.exam_cell_marks_enums import ExamMarksHistoryAction, ExamMarksSubmissionStatus
from app.modules.examinations.exam_cell_marks_models import ExamMarksEntry, ExamMarksHistory, ExamMarksSubmission
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_registration_enums import ExamRegistrationStatus
from app.modules.examinations.exam_cell_registration_models import ExamRegistrationSubject

_PAGE_SIZE = 8


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _subject_label(course_code: str, subject_code: str | None) -> str:
    if subject_code and subject_code.upper() != course_code.upper():
        return subject_code.replace("_", " ").replace("-", " ").title()
    return course_code.replace("_", " ").title()


def _row_status(scripts: int, entered: int, verified: int, submission_status: ExamMarksSubmissionStatus | None) -> tuple[str, str]:
    if scripts == 0:
        return "Not started", "muted"
    if submission_status in (ExamMarksSubmissionStatus.APPROVED, ExamMarksSubmissionStatus.LOCKED):
        if verified >= scripts:
            return "Verified", "success"
    if entered <= 0:
        return "Not started", "muted"
    if verified >= scripts and scripts > 0:
        return "Verified", "success"
    return "In progress", "warning"


async def _build_progress_rows(tenant_id: PydanticObjectId, session: ExamSession) -> list[MarksEntryManagementProgressRow]:
    reg_statuses = [ExamRegistrationStatus.SUBMITTED.value, ExamRegistrationStatus.CONFIRMED.value]
    subjects = await ExamRegistrationSubject.find(
        Eq(ExamRegistrationSubject.tenant_id, tenant_id),
        Eq(ExamRegistrationSubject.exam_session_id, session.id),
    ).to_list()

    scripts_by_course: dict[str, set[str]] = defaultdict(set)
    subject_codes: dict[str, str | None] = {}
    for subj in subjects:
        code = subj.course_code.upper()
        scripts_by_course[code].add(str(subj.student_user_id))
        if subj.subject_code:
            subject_codes[code] = subj.subject_code

    submissions = await ExamMarksSubmission.find(
        Eq(ExamMarksSubmission.tenant_id, tenant_id),
        Eq(ExamMarksSubmission.exam_session_id, session.id),
    ).to_list()
    submission_by_course = {s.course_code.upper(): s for s in submissions}

    faculty_ids = {s.primary_examiner_user_id for s in submissions}
    faculty_names: dict[str, str] = {}
    if faculty_ids:
        faculty_names = {
            str(u.id): u.full_name for u in await User.find(Eq(User.tenant_id, tenant_id), In(User.id, list(faculty_ids))).to_list()
        }

    rows: list[MarksEntryManagementProgressRow] = []
    all_courses = sorted(set(scripts_by_course.keys()) | set(submission_by_course.keys()))
    for course_code in all_courses:
        submission = submission_by_course.get(course_code)
        scripts = len(scripts_by_course.get(course_code, set()))
        entered = 0
        verified = 0
        if submission:
            entries = await ExamMarksEntry.find(
                Eq(ExamMarksEntry.tenant_id, tenant_id),
                Eq(ExamMarksEntry.submission_id, submission.submission_id),
            ).to_list()
            for entry in entries:
                if entry.total_marks is not None:
                    entered += 1
                if entry.locked or submission.status in (ExamMarksSubmissionStatus.APPROVED, ExamMarksSubmissionStatus.LOCKED):
                    if entry.total_marks is not None:
                        verified += 1
            faculty = faculty_names.get(str(submission.primary_examiner_user_id), "—")
            status = submission.status
        else:
            faculty = "—"
            status = None

        status_label, status_tone = _row_status(scripts, entered, verified, status)
        rows.append(
            MarksEntryManagementProgressRow(
                course_code=course_code,
                subject_label=_subject_label(course_code, subject_codes.get(course_code)),
                faculty_label=faculty,
                scripts_count=scripts,
                entered_count=entered,
                verified_count=verified,
                status_label=status_label,
                status_tone=status_tone,
            )
        )
    return rows


async def get_marks_entry_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    session_id: str | None = None,
) -> MarksEntryManagementPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).sort("-registration_start_at").to_list()
    session = _select_session(sessions, session_id, now) or _pick_focus_session(sessions, now=now)
    empty_pagination = PoliciesPagination(
        page=1, page_size=_PAGE_SIZE, total=0, total_pages=0, page_numbers=[], has_previous=False, has_next=False
    )
    if session is None:
        return MarksEntryManagementPageRead(
            page_title="Marks Entry Management",
            page_subtitle="Track marks entry progress",
            **workflow_chrome("marks_entry", session_id),  # type: ignore[arg-type]
            send_reminders_label="Send reminders",
            lock_entry_label="Lock entry",
            sub_nav=examination_marks_assessment_sub_nav("marks-entry-management"),
            progress_section_title="Marks entry progress",
            table_headers=["Subject", "Faculty", "Scripts", "Entered", "Verified", "Status"],
            progress_rows=[],
            showing_label="0 of 0 papers",
            pagination=empty_pagination,
            selected_session_id="",
            footer_disclaimer="Live institutional data · Marks entry · All times IST",
            footer_snapshot_label="Sample snapshot",
            generated_at=now,
        )

    all_rows = await _build_progress_rows(tenant_id, session)
    total = len(all_rows)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages) if total_pages else 1
    start = (page - 1) * _PAGE_SIZE
    page_rows = all_rows[start : start + _PAGE_SIZE]

    panel_empty = empty_state_for_step("marks_entry", session.session_id) if total == 0 else None
    return MarksEntryManagementPageRead(
        page_title="Marks Entry Management",
        page_subtitle=f"Marks entry · {session.name}",
        panel_empty_state=panel_empty,
        **workflow_chrome("marks_entry", session.session_id),  # type: ignore[arg-type]
        send_reminders_label="Send reminders",
        lock_entry_label="Lock entry",
        sub_nav=examination_marks_assessment_sub_nav("marks-entry-management"),
        progress_section_title="Marks entry progress",
        table_headers=["Subject", "Faculty", "Scripts", "Entered", "Verified", "Status"],
        progress_rows=page_rows,
        showing_label=f"{len(page_rows)} of {total:,} papers" if total else "0 of 0 papers",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        selected_session_id=session.session_id,
        footer_disclaimer="Live institutional data · Marks entry · All times IST",
        footer_snapshot_label="Sample snapshot",
        generated_at=now,
    )


async def send_marks_entry_reminders_page(
    scope: AccessScope,
    payload: MarksEntryManagementActionPayload,
) -> MarksEntryManagementPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_CONFIG)
    actor = await User.get(scope.user_id)
    if actor is None:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    tenant_id = require_college_tenant_scope(scope)
    session = await ExamSession.find_one(
        Eq(ExamSession.tenant_id, tenant_id),
        Eq(ExamSession.session_id, payload.session_id),
    )
    if session is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)

    pending = await ExamMarksSubmission.find(
        Eq(ExamMarksSubmission.tenant_id, tenant_id),
        Eq(ExamMarksSubmission.exam_session_id, session.id),
        In(
            ExamMarksSubmission.status,
            [
                ExamMarksSubmissionStatus.DRAFT.value,
                ExamMarksSubmissionStatus.SUBMITTED.value,
                ExamMarksSubmissionStatus.UNDER_MODERATION.value,
            ],
        ),
    ).to_list()
    for submission in pending:
        await ExamMarksHistory(
            tenant_id=tenant_id,
            submission_id=submission.submission_id,
            action=ExamMarksHistoryAction.DRAFT_SAVED,
            actor_id=actor.id,
            note="Marks entry reminder sent",
        ).insert()

    await record_exam_activity(
        tenant_id,
        actor_id=actor.id,
        action="exam_marks_entry.reminders_sent",
        summary=f"Sent {len(pending)} marks entry reminders for session {session.session_id}",
        exam_session_id=session.id,
        metadata={"count": len(pending)},
    )
    return await get_marks_entry_management_page(scope, page=payload.page, session_id=payload.session_id)


async def lock_marks_entry_page(
    scope: AccessScope,
    payload: MarksEntryManagementActionPayload,
) -> MarksEntryManagementPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_PUBLISH)
    actor = await User.get(scope.user_id)
    if actor is None:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    tenant_id = require_college_tenant_scope(scope)
    session = await ExamSession.find_one(
        Eq(ExamSession.tenant_id, tenant_id),
        Eq(ExamSession.session_id, payload.session_id),
    )
    if session is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)

    submissions = await ExamMarksSubmission.find(
        Eq(ExamMarksSubmission.tenant_id, tenant_id),
        Eq(ExamMarksSubmission.exam_session_id, session.id),
    ).to_list()
    now = utcnow()
    for submission in submissions:
        if submission.status == ExamMarksSubmissionStatus.LOCKED:
            continue
        submission.status = ExamMarksSubmissionStatus.LOCKED
        submission.locked_at = now
        submission.updated_at = now
        await submission.save()
        await ExamMarksEntry.find(
            Eq(ExamMarksEntry.tenant_id, tenant_id),
            Eq(ExamMarksEntry.submission_id, submission.submission_id),
        ).update({"$set": {"locked": True, "updated_at": now}})
        await ExamMarksHistory(
            tenant_id=tenant_id,
            submission_id=submission.submission_id,
            action=ExamMarksHistoryAction.LOCKED,
            actor_id=actor.id,
            note="Locked by college admin",
        ).insert()

    await record_exam_activity(
        tenant_id,
        actor_id=actor.id,
        action="exam_marks_entry.locked",
        summary=f"Locked marks entry for session {session.session_id}",
        exam_session_id=session.id,
        metadata={"submissions": len(submissions)},
    )
    return await get_marks_entry_management_page(scope, page=payload.page, session_id=payload.session_id)