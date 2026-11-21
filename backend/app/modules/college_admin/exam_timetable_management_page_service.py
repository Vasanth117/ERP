"""Exam timetable management page (CA 09.03)."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.examination_overview_service import _pick_focus_session
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    ExamTimetableClashBanner,
    ExamTimetableManagementPageRead,
    ExamTimetableManagementRow,
    ExamTimetableManagementActionPayload,
    PoliciesPagination,
    StudentAdminDashboardFilterOption,
)
from app.modules.college_admin.student_administration_dashboard_page_service import _fmt_time_label
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_registration_enums import ExamRegistrationStatus
from app.modules.examinations.exam_cell_registration_models import ExamRegistration, ExamRegistrationSubject
from app.modules.examinations.exam_cell_seating_models import ExamRoom
from app.modules.examinations.exam_cell_timetable_conflict import detect_entry_conflicts, load_timetable_entries
from app.modules.examinations.exam_cell_timetable_enums import ExamTimetableEntryStatus, ExamTimetableStatus
from app.modules.examinations.exam_cell_timetable_models import ExamTimetable, ExamTimetableEntry
from app.modules.examinations.exam_cell_timetable_schemas import (
    ExamTimetableApprovalRequest,
    ExamTimetableCreate,
)
from app.modules.examinations.exam_cell_timetable_service import (
    approve_exam_timetable,
    create_exam_timetable,
    publish_exam_timetable,
    revise_exam_timetable,
    submit_exam_timetable,
)

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 8

_REG_STATUSES = [ExamRegistrationStatus.SUBMITTED.value, ExamRegistrationStatus.CONFIRMED.value]


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _date_label(dt: datetime) -> str:
    local = as_utc_aware(dt).astimezone(_IST)
    return f"{local.day} {local.strftime('%b %Y')}"


def _session_slot_label(entry: ExamTimetableEntry) -> str:
    if entry.session_label:
        return entry.session_label
    if entry.shift_label:
        return entry.shift_label
    hour = as_utc_aware(entry.scheduled_start).astimezone(_IST).hour
    return "FN" if hour < 13 else "AN"


def _select_session(sessions: list[ExamSession], session_id: str | None, now: datetime) -> ExamSession | None:
    if session_id:
        for row in sessions:
            if row.session_id == session_id:
                return row
    return _pick_focus_session(sessions, now=now)


async def _programme_lookup(tenant_id: PydanticObjectId) -> dict[str, AcademicProgramme]:
    rows = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    return {row.programme_code.upper(): row for row in rows}


def _programme_sem_label(entry: ExamTimetableEntry, programmes: dict[str, AcademicProgramme], semester: str) -> str:
    prog_code = (entry.programme_code or "").upper()
    if prog_code in programmes:
        short = programmes[prog_code].programme_code.split("_")[0][:8]
        return f"{short} - {semester}"
    group = entry.student_group_label or ""
    if "-" in group:
        return f"{group.split('-')[0]} - {semester}"
    return f"{prog_code or '—'} - {semester}" if prog_code else "—"


def _hall_label(entry: ExamTimetableEntry, rooms: dict[str, str]) -> str:
    if entry.room_label and entry.room_label in rooms:
        return rooms[entry.room_label]
    if entry.room_label:
        return entry.room_label
    if entry.centre_code:
        return entry.centre_code
    return "—"


def _clash_banner(conflicts: list[dict], *, entries_by_code: dict[str, ExamTimetableEntry]) -> ExamTimetableClashBanner:
    relevant = [
        c
        for c in conflicts
        if c.get("conflict_type")
        in {"student_group_clash", "subject_group_overlap", "room_clash", "duplicate_examination"}
    ]
    if not relevant:
        return ExamTimetableClashBanner(visible=False, headline="", description="", tone="warning")
    count = len(relevant)
    first = relevant[0]
    description = first.get("message") or "Resolve before publishing."
    if first.get("conflict_type") == "student_group_clash":
        entry_payloads = first.get("entries") or []
        names: list[str] = []
        for payload in entry_payloads[:2]:
            code = payload.get("entry_code")
            if code and code in entries_by_code:
                meta = entries_by_code[code].metadata or {}
                names.append(str(meta.get("subject_name") or entries_by_code[code].course_code))
            elif payload.get("course_code"):
                names.append(payload["course_code"])
        group = first.get("student_group_label", "students")
        if len(names) >= 2:
            description = f"{' and '.join(names)} overlap for {group}. Resolve before publishing."
    return ExamTimetableClashBanner(
        visible=True,
        headline=f"{count} clashes found",
        description=description,
        tone="warning",
    )


async def _ensure_timetable(
    scope: AccessScope,
    user: User,
    tenant_id: PydanticObjectId,
    session: ExamSession,
) -> ExamTimetable:
    existing = await ExamTimetable.find_one(
        Eq(ExamTimetable.tenant_id, tenant_id),
        Eq(ExamTimetable.exam_session_id, session.id),
    )
    if existing:
        if existing.status == ExamTimetableStatus.PUBLISHED:
            await revise_exam_timetable(scope, user, existing.id)
            existing = await ExamTimetable.get(existing.id)
        return existing
    created = await create_exam_timetable(
        scope,
        user,
        ExamTimetableCreate(
            exam_session_id=str(session.id),
            title=f"{session.name} timetable",
            shift_labels=["FN", "AN"],
        ),
    )
    doc = await ExamTimetable.find_one(
        Eq(ExamTimetable.tenant_id, tenant_id),
        Eq(ExamTimetable.timetable_id, created.timetable_id),
    )
    if doc is None:
        raise AppError(code="SERVER", message="Failed to create timetable", status_code=500)
    return doc


async def _regenerate_entries(
    scope: AccessScope,
    user: User,
    tenant_id: PydanticObjectId,
    session: ExamSession,
    timetable: ExamTimetable,
) -> None:
    active_entries = await ExamTimetableEntry.find(
        Eq(ExamTimetableEntry.tenant_id, tenant_id),
        Eq(ExamTimetableEntry.timetable_id, timetable.id),
        Eq(ExamTimetableEntry.status, ExamTimetableEntryStatus.ACTIVE),
    ).to_list()
    now = utcnow()
    for entry in active_entries:
        entry.status = ExamTimetableEntryStatus.CANCELLED
        entry.updated_at = now
        await entry.save()

    subjects = await ExamRegistrationSubject.find(
        Eq(ExamRegistrationSubject.tenant_id, tenant_id),
        Eq(ExamRegistrationSubject.exam_session_id, session.id),
    ).to_list()
    if not subjects:
        timetable.updated_at = now
        await timetable.save()
        return

    student_ids = {s.student_user_id for s in subjects}
    records = await StudentRecord.find(
        Eq(StudentRecord.tenant_id, tenant_id),
        In(StudentRecord.user_id, list(student_ids)),
    ).to_list()
    prog_by_user = {r.user_id: (r.programme_code or "ALL").upper() for r in records}

    papers: dict[str, dict] = {}
    for sub in subjects:
        prog = prog_by_user.get(sub.student_user_id, "ALL")
        if sub.course_code not in papers:
            papers[sub.course_code] = {
                "programme_code": prog,
                "subject_code": sub.subject_code or sub.course_code,
                "students": set(),
            }
        papers[sub.course_code]["students"].add(sub.student_user_id)
        if prog != "ALL":
            papers[sub.course_code]["programme_code"] = prog

    by_programme: dict[str, list[str]] = defaultdict(list)
    for course_code, info in sorted(papers.items()):
        by_programme[info["programme_code"]].append(course_code)

    rooms = await ExamRoom.find(
        Eq(ExamRoom.tenant_id, tenant_id),
        Eq(ExamRoom.exam_session_id, session.id),
        Eq(ExamRoom.active, True),
    ).to_list()
    room_labels = [r.room_label for r in rooms] if rooms else ["Main Block"]

    exam_start = as_utc_aware(session.examination_start_at).astimezone(_IST)
    day_cursor = 0
    room_i = 0

    for prog_code, course_list in sorted(by_programme.items()):
        idx = 0
        while idx < len(course_list):
            pair = course_list[idx : idx + 2]
            local_day = (exam_start + timedelta(days=day_cursor)).date()
            slot = "FN" if day_cursor % 2 == 0 else "AN"
            start_hour = 9 if slot == "FN" else 14
            local_start = datetime(local_day.year, local_day.month, local_day.day, start_hour, 0, tzinfo=_IST)
            local_end = local_start + timedelta(hours=3)
            group_label = f"{prog_code}-{session.semester_label}"
            room = room_labels[room_i % len(room_labels)]
            room_i += 1
            for course_code in pair:
                entry = ExamTimetableEntry(
                    tenant_id=tenant_id,
                    timetable_id=timetable.id,
                    entry_code=f"TE-{uuid4().hex[:8].upper()}",
                    course_code=course_code.upper(),
                    subject_code=papers[course_code]["subject_code"],
                    paper_code=papers[course_code]["subject_code"],
                    programme_code=prog_code if prog_code != "ALL" else None,
                    student_group_label=group_label,
                    scheduled_start=local_start.astimezone(timezone.utc),
                    scheduled_end=local_end.astimezone(timezone.utc),
                    duration_minutes=180,
                    shift_label=slot,
                    session_label=slot,
                    room_label=room,
                    centre_code="MAIN",
                    metadata={
                        "subject_name": course_code,
                        "registered_students": len(papers[course_code]["students"]),
                    },
                )
                await entry.insert()
            idx += 2
            day_cursor += 1

    timetable.status = ExamTimetableStatus.DRAFT
    timetable.updated_at = now
    await timetable.save()


async def _publish_timetable_flow(scope: AccessScope, user: User, timetable: ExamTimetable) -> None:
    conflicts = detect_entry_conflicts(await load_timetable_entries(timetable.tenant_id, timetable.id))
    if conflicts:
        raise AppError(
            code="TIMETABLE_CONFLICT",
            message="Resolve timetable conflicts before publishing",
            status_code=409,
        )
    oid = timetable.id
    if timetable.status == ExamTimetableStatus.DRAFT:
        await submit_exam_timetable(scope, user, oid)
        timetable = await ExamTimetable.get(oid)
    if timetable.status == ExamTimetableStatus.IN_REVIEW:
        await approve_exam_timetable(scope, user, oid, ExamTimetableApprovalRequest(note="College admin approval"))
        timetable = await ExamTimetable.get(oid)
    if timetable.status == ExamTimetableStatus.APPROVED:
        await publish_exam_timetable(scope, user, oid)


async def get_exam_timetable_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    session_id: str | None = None,
    programme_code: str | None = None,
) -> ExamTimetableManagementPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).sort("-examination_start_at").to_list()
    session = _select_session(sessions, session_id, now)
    session_options = [
        StudentAdminDashboardFilterOption(value=s.session_id, label=s.name or s.session_code) for s in sessions
    ]

    empty_pagination = PoliciesPagination(
        page=1,
        page_size=_PAGE_SIZE,
        total=0,
        total_pages=0,
        page_numbers=[],
        has_previous=False,
        has_next=False,
    )

    if session is None:
        return ExamTimetableManagementPageRead(
            page_title="Exam Timetable Management",
            page_subtitle="Generate and publish the timetable",
            regenerate_label="Regenerate",
            publish_label="Publish",
            session_filter_label="Exam session",
            programme_filter_label="Programme",
            scope_indicator_label="College scope",
            updated_at_label=_fmt_time_label(now),
            session_options=session_options,
            programme_options=[StudentAdminDashboardFilterOption(value="", label="All programmes")],
            selected_session_id="",
            selected_programme_code="",
            clash_banner=ExamTimetableClashBanner(visible=False, headline="", description="", tone="warning"),
            timetable_section_title="Exam timetable",
            papers_count_label="0 papers",
            table_headers=["Date", "Session", "Subject", "Code", "Programme / sem", "Hall"],
            rows=[],
            showing_label="Showing 0 of 0",
            pagination=empty_pagination,
            timetable_status_label="—",
            publish_enabled=False,
            footer_disclaimer="Live institutional data · Exam timetables · All times IST",
            footer_snapshot_label="Sample snapshot",
            generated_at=now,
        )

    timetable = await ExamTimetable.find_one(
        Eq(ExamTimetable.tenant_id, tenant_id),
        Eq(ExamTimetable.exam_session_id, session.id),
    )
    programmes = await _programme_lookup(tenant_id)
    rooms = await ExamRoom.find(
        Eq(ExamRoom.tenant_id, tenant_id),
        Eq(ExamRoom.exam_session_id, session.id),
    ).to_list()
    room_names = {r.room_label: r.room_label for r in rooms}

    all_entries: list[ExamTimetableEntry] = []
    programme_codes: set[str] = set()
    if timetable:
        all_entries = await ExamTimetableEntry.find(
            Eq(ExamTimetableEntry.tenant_id, tenant_id),
            Eq(ExamTimetableEntry.timetable_id, timetable.id),
            Eq(ExamTimetableEntry.status, ExamTimetableEntryStatus.ACTIVE),
        ).sort("scheduled_start").to_list()
        for entry in all_entries:
            if entry.programme_code:
                programme_codes.add(entry.programme_code.upper())

    prog_filter = (programme_code or "").strip().upper()
    if prog_filter:
        all_entries = [e for e in all_entries if (e.programme_code or "").upper() == prog_filter]

    programme_options = [StudentAdminDashboardFilterOption(value="", label="All programmes")]
    programme_options.extend(
        StudentAdminDashboardFilterOption(
            value=code,
            label=programmes[code].programme_code if code in programmes else code,
        )
        for code in sorted(programme_codes)
    )

    total = len(all_entries)
    total_pages = math.ceil(total / _PAGE_SIZE) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_entries = all_entries[start : start + _PAGE_SIZE]

    entries_by_code = {e.entry_code: e for e in all_entries}
    conflicts: list[dict] = []
    if timetable:
        conflicts = detect_entry_conflicts(await load_timetable_entries(tenant_id, timetable.id))

    rows: list[ExamTimetableManagementRow] = []
    for entry in page_entries:
        meta = entry.metadata or {}
        subject = str(meta.get("subject_name") or entry.course_code)
        rows.append(
            ExamTimetableManagementRow(
                entry_code=entry.entry_code,
                date_label=_date_label(entry.scheduled_start),
                session_label=_session_slot_label(entry),
                subject_label=subject,
                code_label=entry.paper_code or entry.subject_code or entry.course_code,
                programme_sem_label=_programme_sem_label(entry, programmes, session.semester_label),
                hall_label=_hall_label(entry, room_names),
            )
        )

    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)
    clash = _clash_banner(conflicts, entries_by_code=entries_by_code)

    publish_enabled = bool(timetable and total and not conflicts and timetable.status != ExamTimetableStatus.PUBLISHED)
    status_label = timetable.status.value.replace("_", " ").title() if timetable else "No timetable"

    return ExamTimetableManagementPageRead(
        page_title="Exam Timetable Management",
        page_subtitle="Generate and publish the timetable",
        regenerate_label="Regenerate",
        publish_label="Publish",
        session_filter_label="Exam session",
        programme_filter_label="Programme",
        scope_indicator_label="College scope",
        updated_at_label=_fmt_time_label(now),
        session_options=session_options,
        programme_options=programme_options,
        selected_session_id=session.session_id,
        selected_programme_code=prog_filter,
        clash_banner=clash,
        timetable_section_title="Exam timetable",
        papers_count_label=f"{showing_to} of {total:,} papers" if total else "0 papers",
        table_headers=["Date", "Session", "Subject", "Code", "Programme / sem", "Hall"],
        rows=rows,
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
        timetable_status_label=status_label,
        publish_enabled=publish_enabled,
        footer_disclaimer="Live institutional data · Exam timetables · All times IST",
        footer_snapshot_label="Sample snapshot",
        generated_at=now,
    )


async def regenerate_exam_timetable_page(
    scope: AccessScope,
    payload: ExamTimetableManagementActionPayload,
) -> ExamTimetableManagementPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_CONFIG)
    user = await User.get(scope.user_id)
    if user is None:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    tenant_id = require_college_tenant_scope(scope)
    session = await ExamSession.find_one(
        Eq(ExamSession.tenant_id, tenant_id),
        Eq(ExamSession.session_id, payload.session_id),
    )
    if session is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)
    timetable = await _ensure_timetable(scope, user, tenant_id, session)
    await _regenerate_entries(scope, user, tenant_id, session, timetable)
    return await get_exam_timetable_management_page(
        scope,
        page=payload.page,
        session_id=payload.session_id,
        programme_code=payload.programme_code,
    )


async def publish_exam_timetable_page(
    scope: AccessScope,
    payload: ExamTimetableManagementActionPayload,
) -> ExamTimetableManagementPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_PUBLISH)
    user = await User.get(scope.user_id)
    if user is None:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    tenant_id = require_college_tenant_scope(scope)
    session = await ExamSession.find_one(
        Eq(ExamSession.tenant_id, tenant_id),
        Eq(ExamSession.session_id, payload.session_id),
    )
    if session is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)
    timetable = await ExamTimetable.find_one(
        Eq(ExamTimetable.tenant_id, tenant_id),
        Eq(ExamTimetable.exam_session_id, session.id),
    )
    if timetable is None:
        raise AppError(code="NOT_FOUND", message="Generate a timetable before publishing", status_code=404)
    await _publish_timetable_flow(scope, user, timetable)
    return await get_exam_timetable_management_page(
        scope,
        page=payload.page,
        session_id=payload.session_id,
        programme_code=payload.programme_code,
    )