"""Invigilator allocation page (CA 09.07)."""

from __future__ import annotations

import math
from uuid import uuid4
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.exam_registration_management_page_service import _select_session
from app.modules.college_admin.examination_halls_invigilation_nav import examination_halls_invigilation_sub_nav
from app.modules.college_admin.examination_overview_service import _pick_focus_session
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    InvigilatorAllocationActionPayload,
    InvigilatorAllocationDutyRow,
    InvigilatorAllocationPageRead,
    PoliciesPagination,
)
from app.modules.examinations.exam_cell_audit import record_exam_activity
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_seating_enums import ExamDutyHistoryAction, ExamDutyHistoryKind, ExamInvigilatorRole
from app.modules.examinations.exam_cell_seating_models import ExamDutyHistory, ExamInvigilatorAssignment, ExamRoom, ExamSeatingPlan, ExamVenue
from app.modules.examinations.exam_cell_seating_schemas import ExamInvigilatorAssignRequest
from app.modules.examinations.exam_cell_seating_service import assign_invigilator
from app.modules.examinations.exam_cell_timetable_enums import ExamTimetableEntryStatus
from app.modules.examinations.exam_cell_timetable_models import ExamTimetable, ExamTimetableEntry

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 8


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _short_date(dt) -> str:
    local = as_utc_aware(dt).astimezone(_IST)
    return f"{local.day} {local.strftime('%b')}"


def _session_slot(entry: ExamTimetableEntry) -> str:
    if entry.session_label:
        return entry.session_label
    if entry.shift_label:
        return entry.shift_label
    hour = as_utc_aware(entry.scheduled_start).astimezone(_IST).hour
    return "FN" if hour < 13 else "AN"


def _hall_label(room: ExamRoom | None, venues: dict[str, ExamVenue], entry: ExamTimetableEntry) -> str:
    if room is None:
        return entry.room_label or "—"
    venue = venues.get(room.venue_id)
    if venue is None:
        return room.room_label
    return f"{venue.name} · {room.room_label}"


def _matches_slot(assignment: ExamInvigilatorAssignment, entry: ExamTimetableEntry) -> bool:
    if assignment.scheduled_start is None:
        return True
    start = as_utc_aware(assignment.scheduled_start)
    entry_start = as_utc_aware(entry.scheduled_start)
    return abs((start - entry_start).total_seconds()) < 6 * 3600


async def get_invigilator_allocation_page(
    scope: AccessScope,
    *,
    page: int = 1,
    session_id: str | None = None,
) -> InvigilatorAllocationPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).sort("-registration_start_at").to_list()
    session = _select_session(sessions, session_id, now) or _pick_focus_session(sessions, now=now)
    empty_pagination = PoliciesPagination(
        page=1, page_size=_PAGE_SIZE, total=0, total_pages=0, page_numbers=[], has_previous=False, has_next=False
    )
    if session is None:
        return InvigilatorAllocationPageRead(
            page_title="Invigilator Allocation",
            page_subtitle="Duty roster for the session",
            auto_assign_label="Auto-assign",
            publish_roster_label="Publish roster",
            sub_nav=examination_halls_invigilation_sub_nav("invigilator-allocation"),
            duties_section_title="Duties",
            table_headers=["Date", "Session", "Hall", "Invigilator", "Substitute", "Status"],
            duty_rows=[],
            showing_label="0 of 0",
            pagination=empty_pagination,
            selected_session_id="",
            footer_disclaimer="Live institutional data · Invigilator duties · All times IST",
            footer_snapshot_label="Sample snapshot",
            generated_at=now,
        )

    rooms = await ExamRoom.find(
        Eq(ExamRoom.tenant_id, tenant_id),
        Eq(ExamRoom.exam_session_id, session.id),
        Eq(ExamRoom.active, True),
    ).to_list()
    room_by_label = {r.room_label.upper(): r for r in rooms}
    venues = {
        v.venue_id: v
        for v in await ExamVenue.find(Eq(ExamVenue.tenant_id, tenant_id), Eq(ExamVenue.exam_session_id, session.id)).to_list()
    }

    timetables = await ExamTimetable.find(Eq(ExamTimetable.tenant_id, tenant_id), Eq(ExamTimetable.exam_session_id, session.id)).to_list()
    timetable_ids = [t.id for t in timetables]
    entries: list[ExamTimetableEntry] = []
    if timetable_ids:
        entries = await ExamTimetableEntry.find(
            Eq(ExamTimetableEntry.tenant_id, tenant_id),
            In(ExamTimetableEntry.timetable_id, timetable_ids),
            Eq(ExamTimetableEntry.status, ExamTimetableEntryStatus.ACTIVE),
        ).sort("+scheduled_start").to_list()

    plans = await ExamSeatingPlan.find(Eq(ExamSeatingPlan.tenant_id, tenant_id), Eq(ExamSeatingPlan.exam_session_id, session.id)).to_list()
    plan_ids = [p.plan_id for p in plans]
    assignments: list[ExamInvigilatorAssignment] = []
    if plan_ids:
        assignments = await ExamInvigilatorAssignment.find(
            Eq(ExamInvigilatorAssignment.tenant_id, tenant_id),
            In(ExamInvigilatorAssignment.plan_id, plan_ids),
            Eq(ExamInvigilatorAssignment.active, True),
        ).to_list()

    faculty_ids = {a.faculty_user_id for a in assignments}
    faculty_names: dict[str, str] = {}
    if faculty_ids:
        faculty_names = {
            str(u.id): u.full_name
            for u in await User.find(Eq(User.tenant_id, tenant_id), In(User.id, list(faculty_ids))).to_list()
        }

    duty_rows: list[InvigilatorAllocationDutyRow] = []
    for entry in entries:
        room = room_by_label.get((entry.room_label or "").upper()) if entry.room_label else None
        room_id = room.room_id if room else ""
        slot_assignments = [
            a
            for a in assignments
            if a.room_id == room_id and _matches_slot(a, entry)
        ] if room_id else []
        primary = next((a for a in slot_assignments if a.duty_role == ExamInvigilatorRole.INVIGILATOR), None)
        substitute = next((a for a in slot_assignments if a.duty_role == ExamInvigilatorRole.CHIEF), None)
        invigilator_label = faculty_names.get(str(primary.faculty_user_id), "—") if primary else "—"
        substitute_label = faculty_names.get(str(substitute.faculty_user_id), "—") if substitute else "—"
        if primary:
            status_label, status_tone = "Assigned", "success"
        else:
            status_label, status_tone = "Unassigned", "error"
        duty_rows.append(
            InvigilatorAllocationDutyRow(
                duty_key=f"{entry.entry_code}:{room_id or entry.room_label}",
                date_label=_short_date(entry.scheduled_start),
                session_label=_session_slot(entry),
                hall_label=_hall_label(room, venues, entry),
                invigilator_label=invigilator_label,
                substitute_label=substitute_label,
                status_label=status_label,
                status_tone=status_tone,
            )
        )

    total = len(duty_rows)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages) if total_pages else 1
    start = (page - 1) * _PAGE_SIZE
    page_rows = duty_rows[start : start + _PAGE_SIZE]

    return InvigilatorAllocationPageRead(
        page_title="Invigilator Allocation",
        page_subtitle="Duty roster for the session",
        auto_assign_label="Auto-assign",
        publish_roster_label="Publish roster",
        sub_nav=examination_halls_invigilation_sub_nav("invigilator-allocation"),
        duties_section_title="Duties",
        table_headers=["Date", "Session", "Hall", "Invigilator", "Substitute", "Status"],
        duty_rows=page_rows,
        showing_label=f"{len(page_rows)} of {total:,}" if total else "0 of 0",
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
        footer_disclaimer="Live institutional data · Invigilator duties · All times IST",
        footer_snapshot_label="Sample snapshot",
        generated_at=now,
    )


async def auto_assign_invigilators_page(
    scope: AccessScope,
    payload: InvigilatorAllocationActionPayload,
) -> InvigilatorAllocationPageRead:
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

    plan = await ExamSeatingPlan.find_one(
        Eq(ExamSeatingPlan.tenant_id, tenant_id),
        Eq(ExamSeatingPlan.exam_session_id, session.id),
    )
    if plan is None:
        raise AppError(code="VALIDATION_ERROR", message="Create a seating plan before assigning invigilators", status_code=422)

    faculty = await User.find(Eq(User.tenant_id, tenant_id), Eq(User.role, Role.FACULTY)).sort("+full_name").to_list()
    if not faculty:
        raise AppError(code="VALIDATION_ERROR", message="No faculty available for invigilation", status_code=422)

    rooms = await ExamRoom.find(
        Eq(ExamRoom.tenant_id, tenant_id),
        Eq(ExamRoom.exam_session_id, session.id),
        Eq(ExamRoom.active, True),
    ).to_list()
    room_by_label = {r.room_label.upper(): r for r in rooms}

    timetables = await ExamTimetable.find(Eq(ExamTimetable.tenant_id, tenant_id), Eq(ExamTimetable.exam_session_id, session.id)).to_list()
    timetable_ids = [t.id for t in timetables]
    if not timetable_ids:
        return await get_invigilator_allocation_page(scope, page=payload.page, session_id=payload.session_id)

    entries = await ExamTimetableEntry.find(
        Eq(ExamTimetableEntry.tenant_id, tenant_id),
        In(ExamTimetableEntry.timetable_id, timetable_ids),
        Eq(ExamTimetableEntry.status, ExamTimetableEntryStatus.ACTIVE),
    ).sort("+scheduled_start").to_list()

    existing = await ExamInvigilatorAssignment.find(
        Eq(ExamInvigilatorAssignment.tenant_id, tenant_id),
        Eq(ExamInvigilatorAssignment.plan_id, plan.plan_id),
        Eq(ExamInvigilatorAssignment.active, True),
    ).to_list()
    assigned_faculty = {str(a.faculty_user_id) for a in existing}
    faculty_index = 0

    for entry in entries:
        if not entry.room_label:
            continue
        room = room_by_label.get(entry.room_label.upper())
        if room is None:
            continue
        has_primary = any(
            a.room_id == room.room_id
            and a.duty_role == ExamInvigilatorRole.INVIGILATOR
            and _matches_slot(a, entry)
            for a in existing
        )
        if has_primary:
            continue
        while faculty_index < len(faculty) and str(faculty[faculty_index].id) in assigned_faculty:
            faculty_index += 1
        if faculty_index >= len(faculty):
            faculty_index = 0
        pick = faculty[faculty_index]
        faculty_index += 1
        assigned_faculty.add(str(pick.id))
        try:
            created = await assign_invigilator(
                scope,
                actor,
                ExamInvigilatorAssignRequest(
                    plan_id=plan.plan_id,
                    room_id=room.room_id,
                    faculty_user_id=str(pick.id),
                    duty_role=ExamInvigilatorRole.INVIGILATOR,
                    scheduled_start=entry.scheduled_start,
                    scheduled_end=entry.scheduled_end,
                ),
            )
            doc = await ExamInvigilatorAssignment.find_one(
                Eq(ExamInvigilatorAssignment.tenant_id, tenant_id),
                Eq(ExamInvigilatorAssignment.assignment_id, created.assignment_id),
            )
            if doc is not None:
                existing.append(doc)
        except AppError as exc:
            if exc.code != "CONFLICT":
                raise

        has_sub = any(
            a.room_id == room.room_id
            and a.duty_role == ExamInvigilatorRole.CHIEF
            and _matches_slot(a, entry)
            for a in existing
            if a
        )
        if not has_sub and faculty_index < len(faculty):
            sub = faculty[faculty_index]
            faculty_index += 1
            try:
                await assign_invigilator(
                    scope,
                    actor,
                    ExamInvigilatorAssignRequest(
                        plan_id=plan.plan_id,
                        room_id=room.room_id,
                        faculty_user_id=str(sub.id),
                        duty_role=ExamInvigilatorRole.CHIEF,
                        scheduled_start=entry.scheduled_start,
                        scheduled_end=entry.scheduled_end,
                    ),
                )
            except AppError as exc:
                if exc.code != "CONFLICT":
                    raise

    return await get_invigilator_allocation_page(scope, page=payload.page, session_id=payload.session_id)


async def publish_invigilator_roster_page(
    scope: AccessScope,
    payload: InvigilatorAllocationActionPayload,
) -> InvigilatorAllocationPageRead:
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

    plans = await ExamSeatingPlan.find(Eq(ExamSeatingPlan.tenant_id, tenant_id), Eq(ExamSeatingPlan.exam_session_id, session.id)).to_list()
    plan_ids = [p.plan_id for p in plans]
    if not plan_ids:
        return await get_invigilator_allocation_page(scope, page=payload.page, session_id=payload.session_id)

    assignments = await ExamInvigilatorAssignment.find(
        Eq(ExamInvigilatorAssignment.tenant_id, tenant_id),
        In(ExamInvigilatorAssignment.plan_id, plan_ids),
        Eq(ExamInvigilatorAssignment.active, True),
    ).to_list()
    for assignment in assignments:
        await ExamDutyHistory(
            tenant_id=tenant_id,
            history_id=f"edh_{uuid4().hex[:10]}",
            kind=ExamDutyHistoryKind.INVIGILATION,
            action=ExamDutyHistoryAction.PUBLISHED,
            plan_id=assignment.plan_id,
            exam_session_id=session.id,
            resource_id=assignment.assignment_id,
            actor_id=actor.id,
            note="Roster published",
        ).insert()

    await record_exam_activity(
        tenant_id,
        actor_id=actor.id,
        action="exam_invigilator_roster.published",
        summary=f"Published invigilator roster for session {session.session_id}",
        exam_session_id=session.id,
        metadata={"assignments": len(assignments)},
    )

    return await get_invigilator_allocation_page(scope, page=payload.page, session_id=payload.session_id)