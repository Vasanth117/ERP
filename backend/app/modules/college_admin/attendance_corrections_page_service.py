"""Attendance correction requests list and approval pages (CA 08.08 / 08.09)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.attendance.enums import AttendanceCorrectionStatus, AttendanceMarkStatus
from app.modules.attendance.models import AttendanceCorrectionRequest, AttendanceSession
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import FacultyRecord
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.models import InstitutionSettings
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AttendanceApprovalPageRead,
    AttendanceCorrectionApprovalStep,
    AttendanceCorrectionRequestTableRow,
    AttendanceCorrectionRequestsPageRead,
    InstitutionFieldOption,
    UserDashboardKpi,
)
from app.modules.faculty.models import FacultyProfile

_IST = ZoneInfo("Asia/Kolkata")
_LIST_LIMIT = 10

_DECISION_OPTIONS = [
    InstitutionFieldOption(value=AttendanceCorrectionStatus.APPROVED.value, label="Approve"),
    InstitutionFieldOption(value=AttendanceCorrectionStatus.REJECTED.value, label="Reject"),
]


def _fmt_snapshot(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Sample snapshot · %d %b %Y, %H:%M IST")


def _fmt_time_label(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Updated %H:%M IST")


def _fmt_session_date(session_date) -> str:
    return datetime.combine(session_date, datetime.min.time(), tzinfo=_IST).strftime("%d %b %Y")


def _fmt_step_date(dt: datetime | None) -> str:
    if dt is None:
        return "Pending"
    return as_utc_aware(dt).astimezone(_IST).strftime("%d %b")


def _request_code(created_at: datetime, doc_id: PydanticObjectId) -> str:
    stamp = f"{created_at.year % 100:02d}{created_at.month:02d}"
    suffix = str(doc_id)[-3:].upper().replace("-", "0")[:3]
    digits = "".join(ch for ch in suffix if ch.isdigit())
    if not digits:
        digits = f"{int(str(doc_id)[-6:], 16) % 1000:03d}"
    return f"ACR-{stamp}-{digits[:3]}"


def _status_presentation(status: AttendanceCorrectionStatus, *, endorsed: bool, requires_college: bool) -> tuple[str, str]:
    if status == AttendanceCorrectionStatus.PENDING:
        if requires_college and endorsed:
            return "Awaiting college", "warning"
        return "Pending review", "warning"
    if status == AttendanceCorrectionStatus.APPROVED:
        return "Approved", "success"
    if status == AttendanceCorrectionStatus.REJECTED:
        return "Rejected", "error"
    return status.value.replace("_", " ").title(), "muted"


def _mark_status_label(status: AttendanceMarkStatus | None) -> str:
    if status is None:
        return "present"
    return status.value.replace("_", " ")


async def _requires_college_approval(tenant_id: PydanticObjectId) -> bool:
    inst_settings = await InstitutionSettings.find_one(Eq(InstitutionSettings.tenant_id, tenant_id))
    return bool((inst_settings.settings or {}).get("attendance_correction_requires_college_approval", False))


async def _faculty_display(
    tenant_id: PydanticObjectId,
    faculty_user_id: PydanticObjectId,
    users_by_id: dict[PydanticObjectId, User],
    profiles_by_user: dict[PydanticObjectId, FacultyProfile],
) -> str:
    user = users_by_id.get(faculty_user_id)
    if user and user.full_name:
        return user.full_name
    return "Faculty"


async def _change_summary(
    tenant_id: PydanticObjectId,
    request: AttendanceCorrectionRequest,
) -> str:
    peers = await AttendanceCorrectionRequest.find(
        Eq(AttendanceCorrectionRequest.tenant_id, tenant_id),
        Eq(AttendanceCorrectionRequest.session_id, request.session_id),
        Eq(AttendanceCorrectionRequest.status, AttendanceCorrectionStatus.PENDING),
    ).to_list()
    mark = _mark_status_label(request.requested_status)
    count = len(peers) if len(peers) > 1 else (1 if request.student_user_id else 0)
    if count > 1:
        return f"{count} students marked {mark}"
    if request.student_user_id:
        return f"1 student marked {mark}"
    if request.requested_status:
        return f"Students marked {mark}"
    return "Attendance correction requested"


def _class_label(session: AttendanceSession) -> str:
    return f"{session.course_code} · {session.section}"


def _approval_steps(
    *,
    request: AttendanceCorrectionRequest,
    department_label: str | None,
    requires_college: bool,
) -> list[AttendanceCorrectionApprovalStep]:
    steps: list[AttendanceCorrectionApprovalStep] = [
        AttendanceCorrectionApprovalStep(
            key="faculty_request",
            label="Faculty request",
            status_label=_fmt_step_date(request.created_at),
            tone="success",
        ),
    ]
    hod_label = f"HOD, {department_label}" if department_label else "HOD"
    if request.department_endorsed_at:
        steps.append(
            AttendanceCorrectionApprovalStep(
                key="hod",
                label=hod_label,
                status_label=_fmt_step_date(request.department_endorsed_at),
                tone="success",
            ),
        )
    elif requires_college and department_label:
        steps.append(
            AttendanceCorrectionApprovalStep(
                key="hod",
                label=hod_label,
                status_label="Pending",
                tone="warning",
            ),
        )
    college_label = "Pending"
    college_tone = "warning"
    if request.status == AttendanceCorrectionStatus.APPROVED:
        college_label = _fmt_step_date(request.resolved_at)
        college_tone = "success"
    elif request.status == AttendanceCorrectionStatus.REJECTED:
        college_label = _fmt_step_date(request.resolved_at)
        college_tone = "error"
    steps.append(
        AttendanceCorrectionApprovalStep(
            key="college_admin",
            label="College Admin",
            status_label=college_label,
            tone=college_tone,
        ),
    )
    return steps


async def _load_context(tenant_id: PydanticObjectId, requests: list[AttendanceCorrectionRequest]):
    faculty_ids = {r.faculty_user_id for r in requests}
    session_ids = {r.session_id for r in requests}
    users = await User.find(In(User.id, list(faculty_ids))).to_list() if faculty_ids else []
    users_by_id = {u.id: u for u in users if u.id is not None}
    profiles = await FacultyProfile.find(In(FacultyProfile.user_id, list(faculty_ids))).to_list() if faculty_ids else []
    profiles_by_user = {p.user_id: p for p in profiles}
    sessions = await AttendanceSession.find(In(AttendanceSession.id, list(session_ids))).to_list() if session_ids else []
    sessions_by_id = {s.id: s for s in sessions if s.id is not None}
    faculty_records = (
        await FacultyRecord.find(In(FacultyRecord.user_id, list(faculty_ids))).to_list() if faculty_ids else []
    )
    dept_ids = {fr.department_id for fr in faculty_records if fr.department_id}
    departments = (
        await InstitutionDepartment.find(In(InstitutionDepartment.id, list(dept_ids))).to_list() if dept_ids else []
    )
    dept_by_id = {d.id: d for d in departments if d.id is not None}
    dept_by_faculty: dict[PydanticObjectId, InstitutionDepartment | None] = {}
    for fr in faculty_records:
        dept_by_faculty[fr.user_id] = dept_by_id.get(fr.department_id) if fr.department_id else None
    return users_by_id, profiles_by_user, sessions_by_id, dept_by_faculty


async def get_attendance_correction_requests_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _LIST_LIMIT,
) -> AttendanceCorrectionRequestsPageRead:
    authorize(scope, Permission.ATTENDANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    requires_college = await _requires_college_approval(tenant_id)

    week_start = datetime.combine(
        (now - timedelta(days=now.weekday())).date(),
        datetime.min.time(),
        tzinfo=timezone.utc,
    )
    pending_all = await AttendanceCorrectionRequest.find(
        Eq(AttendanceCorrectionRequest.tenant_id, tenant_id),
        Eq(AttendanceCorrectionRequest.status, AttendanceCorrectionStatus.PENDING),
    ).to_list()
    awaiting_hod = sum(1 for r in pending_all if requires_college and r.department_endorsed_at is None)
    pending_college = sum(1 for r in pending_all if not requires_college or r.department_endorsed_at is not None)
    approved_rows = await AttendanceCorrectionRequest.find(
        Eq(AttendanceCorrectionRequest.tenant_id, tenant_id),
        Eq(AttendanceCorrectionRequest.status, AttendanceCorrectionStatus.APPROVED),
    ).to_list()
    approved_week = sum(1 for r in approved_rows if r.resolved_at and r.resolved_at >= week_start)

    kpis = [
        UserDashboardKpi(
            key="pending_review",
            label="Pending review",
            value=str(pending_college),
            hint_line="College queue",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="awaiting_hod",
            label="Awaiting HoD approval",
            value=str(awaiting_hod),
            hint_line="Department",
            hint_tone="warning",
        ),
        UserDashboardKpi(
            key="approved_week",
            label="Approved this week",
            value=str(approved_week),
            hint_line="This week",
            hint_tone="success",
        ),
    ]

    query = AttendanceCorrectionRequest.find(Eq(AttendanceCorrectionRequest.tenant_id, tenant_id)).sort("-created_at")
    rows = await query.to_list()
    visible_pool = [
        r
        for r in rows
        if r.status == AttendanceCorrectionStatus.PENDING
        and (not requires_college or r.department_endorsed_at is not None)
    ]
    if not visible_pool:
        visible_pool = [r for r in rows if r.status == AttendanceCorrectionStatus.PENDING][:page_size]

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total = len(visible_pool)
    start = (page - 1) * page_size
    page_rows = visible_pool[start : start + page_size]

    users_by_id, profiles_by_user, sessions_by_id, dept_by_faculty = await _load_context(tenant_id, page_rows)

    table_rows: list[AttendanceCorrectionRequestTableRow] = []
    for req in page_rows:
        session = sessions_by_id.get(req.session_id)
        faculty_label = await _faculty_display(tenant_id, req.faculty_user_id, users_by_id, profiles_by_user)
        class_label = _class_label(session) if session else "—"
        session_date = _fmt_session_date(session.session_date) if session else "—"
        change_summary = await _change_summary(tenant_id, req)
        status_label, status_tone = _status_presentation(
            req.status,
            endorsed=req.department_endorsed_at is not None,
            requires_college=requires_college,
        )
        code = _request_code(req.created_at, req.id)
        table_rows.append(
            AttendanceCorrectionRequestTableRow(
                row_key=str(req.id),
                request_code=code,
                faculty_label=faculty_label,
                class_label=class_label,
                session_date_label=session_date,
                change_summary=change_summary,
                status_label=status_label,
                status_tone=status_tone,
                review_href=f"/college-admin/attendance/attendance-approval?request_id={req.id}",
                review_label="Review",
            ),
        )

    return AttendanceCorrectionRequestsPageRead(
        page_title="Attendance Correction Requests",
        page_subtitle="Faculty-submitted attendance changes awaiting institutional review",
        updated_at_label=_fmt_time_label(now),
        kpis=kpis,
        requests_table_title="Correction requests",
        requests_table_headers=["Request", "Faculty", "Class", "Date", "Change", "Status", "Action"],
        request_rows=table_rows,
        requests_table_footer_label=f"{len(table_rows)} of {total}",
        footer_disclaimer="Illustrative data only · No live student, faculty or finance records · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )


async def get_attendance_approval_page(scope: AccessScope, *, request_id: str | None = None) -> AttendanceApprovalPageRead:
    authorize(scope, Permission.ATTENDANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    requires_college = await _requires_college_approval(tenant_id)

    query = AttendanceCorrectionRequest.find(
        Eq(AttendanceCorrectionRequest.tenant_id, tenant_id),
        Eq(AttendanceCorrectionRequest.status, AttendanceCorrectionStatus.PENDING),
    ).sort("-created_at")
    pending = await query.to_list()
    pool = [r for r in pending if not requires_college or r.department_endorsed_at is not None]
    if not pool:
        pool = pending

    selected: AttendanceCorrectionRequest | None = None
    if request_id:
        oid = to_object_id(request_id, "request_id")
        selected = await AttendanceCorrectionRequest.get(oid)
        if selected is None or selected.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="Correction request not found", status_code=404)
    elif pool:
        selected = pool[0]

    if selected is None:
        return AttendanceApprovalPageRead(
            page_title="Attendance Approval",
            selected_request_id=None,
            request_code="—",
            back_href="/college-admin/attendance/attendance-correction-requests",
            back_label="Back to requests",
            reject_label="Reject",
            approve_label="Approve",
            request_card_title="Request",
            faculty_field_label="Faculty",
            faculty_label="—",
            class_field_label="Class",
            class_label="—",
            date_field_label="Date",
            session_date_label="—",
            change_field_label="Change",
            change_summary="—",
            reason_field_label="Reason",
            reason_text="—",
            decision_card_title="Decision",
            decision_field_label="Decision",
            decision_required=True,
            decision_options=_DECISION_OPTIONS,
            selected_decision=AttendanceCorrectionStatus.APPROVED.value,
            remarks_field_label="Remarks",
            remarks_placeholder="Add remarks for this decision",
            remarks_value="",
            approval_route_title="Approval route",
            approval_steps=[],
            can_decide=False,
            decide_blocked_message="No pending correction requests",
            footer_disclaimer="Illustrative data only · No live student, faculty or finance records · All times IST",
            footer_snapshot_label=_fmt_snapshot(now),
            generated_at=now,
        )

    users_by_id, profiles_by_user, sessions_by_id, dept_by_faculty = await _load_context(tenant_id, [selected])
    session = sessions_by_id.get(selected.session_id)
    faculty_label = await _faculty_display(tenant_id, selected.faculty_user_id, users_by_id, profiles_by_user)
    dept = dept_by_faculty.get(selected.faculty_user_id)
    dept_label = (dept.department_code or dept.name) if dept else None

    can_decide = selected.status == AttendanceCorrectionStatus.PENDING
    blocked: str | None = None
    if requires_college and dept and not selected.department_endorsed_at:
        can_decide = False
        blocked = "Awaiting department head endorsement before college can approve."

    return AttendanceApprovalPageRead(
        page_title="Attendance Approval",
        selected_request_id=str(selected.id),
        request_code=_request_code(selected.created_at, selected.id),
        back_href="/college-admin/attendance/attendance-correction-requests",
        back_label="Back to requests",
        reject_label="Reject",
        approve_label="Approve",
        request_card_title="Request",
        faculty_field_label="Faculty",
        faculty_label=faculty_label,
        class_field_label="Class",
        class_label=_class_label(session) if session else "—",
        date_field_label="Date",
        session_date_label=_fmt_session_date(session.session_date) if session else "—",
        change_field_label="Change",
        change_summary=await _change_summary(tenant_id, selected),
        reason_field_label="Reason",
        reason_text=selected.reason,
        decision_card_title="Decision",
        decision_field_label="Decision",
        decision_required=True,
        decision_options=_DECISION_OPTIONS,
        selected_decision=AttendanceCorrectionStatus.APPROVED.value,
        remarks_field_label="Remarks",
        remarks_placeholder="Add remarks for this decision",
        remarks_value=selected.reviewer_note or "",
        approval_route_title="Approval route",
        approval_steps=_approval_steps(
            request=selected,
            department_label=dept_label,
            requires_college=requires_college,
        ),
        can_decide=can_decide,
        decide_blocked_message=blocked,
        footer_disclaimer="Illustrative data only · No live student, faculty or finance records · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )