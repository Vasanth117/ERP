"""Examination hall & seating management page (CA 09.07)."""

from __future__ import annotations

import math
from collections import defaultdict

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.exam_registration_management_page_service import _select_session
from app.modules.college_admin.examination_halls_invigilation_nav import examination_halls_invigilation_sub_nav
from app.modules.college_admin.examination_workflow import empty_state_for_step, workflow_chrome
from app.modules.college_admin.examination_overview_service import _pick_focus_session
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    ExaminationHallSeatingActionPayload,
    ExaminationHallSeatingHallRow,
    ExaminationHallSeatingManagementPageRead,
    ExaminationHallSeatingSeatUsageItem,
    PoliciesPagination,
)
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_seating_enums import (
    ExamSeatingAllocationStatus,
    ExamSeatingPlanStatus,
    ExamSeatingPolicy,
)
from app.modules.examinations.exam_cell_seating_models import (
    ExamRoom,
    ExamSeatingAllocation,
    ExamSeatingPlan,
    ExamVenue,
)
from app.modules.examinations.exam_cell_seating_schemas import ExamSeatingAllocateRequest, ExamSeatingPlanCreate
from app.modules.examinations.exam_cell_seating_service import allocate_seating, create_seating_plan, publish_seating_plan
from app.modules.examinations.exam_cell_timetable_enums import ExamTimetableEntryStatus
from app.modules.examinations.exam_cell_timetable_models import ExamTimetable, ExamTimetableEntry

_PAGE_SIZE = 8


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _hall_label(room: ExamRoom, venues: dict[str, ExamVenue]) -> str:
    venue = venues.get(room.venue_id)
    if venue is None:
        return room.room_label
    if room.room_label.upper().startswith(venue.name.upper()):
        return room.room_label
    return f"{venue.name} · {room.room_label}"


async def _session_master_plan(tenant_id: PydanticObjectId, session_oid: PydanticObjectId, scope: AccessScope, actor: User) -> ExamSeatingPlan:
    plan = await ExamSeatingPlan.find_one(
        Eq(ExamSeatingPlan.tenant_id, tenant_id),
        Eq(ExamSeatingPlan.exam_session_id, session_oid),
        In(ExamSeatingPlan.status, [ExamSeatingPlanStatus.DRAFT, ExamSeatingPlanStatus.PENDING_APPROVAL]),
    )
    if plan is not None:
        return plan
    read = await create_seating_plan(
        scope,
        actor,
        ExamSeatingPlanCreate(
            exam_session_id=str(session_oid),
            title="Session seating plan",
            seating_policy=ExamSeatingPolicy.MIXED,
        ),
    )
    doc = await ExamSeatingPlan.find_one(Eq(ExamSeatingPlan.tenant_id, tenant_id), Eq(ExamSeatingPlan.plan_id, read.plan_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Seating plan not found after create", status_code=500)
    return doc


async def get_examination_hall_seating_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    session_id: str | None = None,
) -> ExaminationHallSeatingManagementPageRead:
    authorize(scope, Permission.EXAMINATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).sort("-registration_start_at").to_list()
    session = _select_session(sessions, session_id, now) or _pick_focus_session(sessions, now=now)
    empty_pagination = PoliciesPagination(
        page=1, page_size=_PAGE_SIZE, total=0, total_pages=0, page_numbers=[], has_previous=False, has_next=False
    )
    base_empty = ExaminationHallSeatingManagementPageRead(
        page_title="Examination Hall & Seating Management",
        page_subtitle="Assign halls and generate seating",
        **workflow_chrome("assign_halls", session_id),  # type: ignore[arg-type]
        auto_allocate_label="Auto-allocate",
        confirm_label="Confirm",
        sub_nav=examination_halls_invigilation_sub_nav("examination-hall-seating-management"),
        halls_section_title="Halls",
        seat_usage_section_title="Seat usage",
        table_headers=["Hall", "Capacity", "Allocated", "Papers", "Status"],
        hall_rows=[],
        seat_usage_items=[],
        showing_label="Showing 0 of 0",
        pagination=empty_pagination,
        selected_session_id="",
        footer_disclaimer="Live institutional data · Exam halls & seating · All times IST",
        footer_snapshot_label="Sample snapshot",
        generated_at=now,
    )
    if session is None:
        return base_empty

    rooms = await ExamRoom.find(
        Eq(ExamRoom.tenant_id, tenant_id),
        Eq(ExamRoom.exam_session_id, session.id),
        Eq(ExamRoom.active, True),
    ).sort("+room_label").to_list()
    venues = {
        v.venue_id: v
        for v in await ExamVenue.find(
            Eq(ExamVenue.tenant_id, tenant_id),
            Eq(ExamVenue.exam_session_id, session.id),
        ).to_list()
    }

    allocations = await ExamSeatingAllocation.find(
        Eq(ExamSeatingAllocation.tenant_id, tenant_id),
        Eq(ExamSeatingAllocation.exam_session_id, session.id),
        In(
            ExamSeatingAllocation.status,
            [ExamSeatingAllocationStatus.ALLOCATED, ExamSeatingAllocationStatus.CHANGED],
        ),
    ).to_list()
    alloc_by_room: dict[str, int] = defaultdict(int)
    for row in allocations:
        alloc_by_room[row.room_id] += 1

    timetables = await ExamTimetable.find(Eq(ExamTimetable.tenant_id, tenant_id), Eq(ExamTimetable.exam_session_id, session.id)).to_list()
    timetable_ids = [t.id for t in timetables]
    papers_by_room_label: dict[str, int] = defaultdict(int)
    if timetable_ids:
        entries = await ExamTimetableEntry.find(
            Eq(ExamTimetableEntry.tenant_id, tenant_id),
            In(ExamTimetableEntry.timetable_id, timetable_ids),
            Eq(ExamTimetableEntry.status, ExamTimetableEntryStatus.ACTIVE),
        ).to_list()
        for entry in entries:
            if entry.room_label:
                papers_by_room_label[entry.room_label.upper()] += 1

    hall_rows: list[ExaminationHallSeatingHallRow] = []
    for room in rooms:
        allocated = alloc_by_room.get(room.room_id, 0)
        papers = papers_by_room_label.get(room.room_label.upper(), 0)
        if allocated > 0:
            status_label, status_tone = "Allocated", "success"
        else:
            status_label, status_tone = "Unassigned", "warning"
        capacity = room.usable_seating_capacity
        hall_rows.append(
            ExaminationHallSeatingHallRow(
                room_id=room.room_id,
                hall_label=_hall_label(room, venues),
                capacity=capacity,
                allocated_count=allocated,
                papers_count=papers,
                status_label=status_label,
                status_tone=status_tone,
            )
        )

    total = len(hall_rows)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages) if total_pages else 1
    start = (page - 1) * _PAGE_SIZE
    page_rows = hall_rows[start : start + _PAGE_SIZE]

    seat_usage = []
    for row in page_rows:
        cap = max(row.capacity, 1)
        pct = min(100.0, round(100.0 * row.allocated_count / cap, 1))
        seat_usage.append(
            ExaminationHallSeatingSeatUsageItem(
                hall_label=row.hall_label,
                allocated_count=row.allocated_count,
                capacity=row.capacity,
                usage_label=f"{row.allocated_count} of {row.capacity}",
                usage_percent=pct,
            )
        )

    showing = f"{len(page_rows)} of {total:,} halls" if total else "0 of 0 halls"
    panel_empty = empty_state_for_step("assign_halls", session.session_id) if total == 0 else None
    chrome = workflow_chrome("assign_halls", session.session_id)
    return ExaminationHallSeatingManagementPageRead(
        page_title="Examination Hall & Seating Management",
        page_subtitle=f"{chrome['step_progress_label']} · {session.name}",
        panel_empty_state=panel_empty,
        **chrome,  # type: ignore[arg-type]
        auto_allocate_label="Auto-allocate",
        confirm_label="Confirm",
        sub_nav=examination_halls_invigilation_sub_nav("examination-hall-seating-management"),
        halls_section_title="Halls",
        seat_usage_section_title="Seat usage",
        table_headers=["Hall", "Capacity", "Allocated", "Papers", "Status"],
        hall_rows=page_rows,
        seat_usage_items=seat_usage,
        showing_label=showing,
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
        footer_disclaimer="Live institutional data · Exam halls & seating · All times IST",
        footer_snapshot_label="Sample snapshot",
        generated_at=now,
    )


async def auto_allocate_hall_seating_page(
    scope: AccessScope,
    payload: ExaminationHallSeatingActionPayload,
) -> ExaminationHallSeatingManagementPageRead:
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

    plans = await ExamSeatingPlan.find(
        Eq(ExamSeatingPlan.tenant_id, tenant_id),
        Eq(ExamSeatingPlan.exam_session_id, session.id),
        In(ExamSeatingPlan.status, [ExamSeatingPlanStatus.DRAFT, ExamSeatingPlanStatus.PENDING_APPROVAL]),
    ).to_list()
    if not plans:
        await _session_master_plan(tenant_id, session.id, scope, user)
        plans = await ExamSeatingPlan.find(
            Eq(ExamSeatingPlan.tenant_id, tenant_id),
            Eq(ExamSeatingPlan.exam_session_id, session.id),
            In(ExamSeatingPlan.status, [ExamSeatingPlanStatus.DRAFT, ExamSeatingPlanStatus.PENDING_APPROVAL]),
        ).to_list()

    for plan in plans:
        await allocate_seating(
            scope,
            user,
            ExamSeatingAllocateRequest(plan_id=plan.plan_id, course_code=plan.course_code),
        )

    return await get_examination_hall_seating_management_page(scope, page=payload.page, session_id=payload.session_id)


async def confirm_hall_seating_page(
    scope: AccessScope,
    payload: ExaminationHallSeatingActionPayload,
) -> ExaminationHallSeatingManagementPageRead:
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

    plans = await ExamSeatingPlan.find(
        Eq(ExamSeatingPlan.tenant_id, tenant_id),
        Eq(ExamSeatingPlan.exam_session_id, session.id),
        In(ExamSeatingPlan.status, [ExamSeatingPlanStatus.DRAFT, ExamSeatingPlanStatus.PENDING_APPROVAL]),
    ).to_list()
    for plan in plans:
        count = await ExamSeatingAllocation.find(
            Eq(ExamSeatingAllocation.tenant_id, tenant_id),
            Eq(ExamSeatingAllocation.plan_id, plan.plan_id),
            In(ExamSeatingAllocation.status, [ExamSeatingAllocationStatus.ALLOCATED, ExamSeatingAllocationStatus.CHANGED]),
        ).count()
        if count > 0:
            try:
                await publish_seating_plan(scope, user, plan.plan_id)
            except AppError as exc:
                if exc.code != "INVALID_STATE":
                    raise

    return await get_examination_hall_seating_management_page(scope, page=payload.page, session_id=payload.session_id)