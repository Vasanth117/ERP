"""Attendance monitoring live view (CA 08.06)."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE, In, LTE

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.modules.academics.models import ClassSession, PendingAttendanceSubmission
from app.modules.attendance.enums import AttendanceSessionStatus
from app.modules.attendance.models import AttendanceSession
from app.modules.auth.models import User
from app.modules.college_admin.attendance_admin_models import (
    AttendancePolicyAudience,
    AttendanceSubmissionMonitoring,
    InstitutionAttendancePolicy,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import AttendanceMonitoringPageRead, AttendanceMonitoringTableRow, UserDashboardKpi
from app.modules.department_admin.models import DepartmentRequestStatus, DepartmentSubstituteRequest

_IST = ZoneInfo("Asia/Kolkata")
_TABLE_LIMIT = 10


def _fmt_time_label(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Updated %H:%M IST")


def _fmt_snapshot(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Snapshot · %d %b %Y, %H:%M IST")


def _format_clock(dt: datetime) -> str:
    local = as_utc_aware(dt).astimezone(_IST)
    return local.strftime("%H:%M")


def _delay_label(anchor: datetime, now: datetime) -> str:
    delta = now - as_utc_aware(anchor)
    if delta.total_seconds() < 0:
        return "—"
    minutes = int(delta.total_seconds() // 60)
    if minutes >= 60:
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours} h {mins:02d}" if mins else f"{hours} h"
    return f"{minutes} min"


def _action_for(*, monitoring_status: str | None, due_at: datetime | None, now: datetime) -> tuple[str, str]:
    if monitoring_status == "reminder_sent":
        return "Reminder sent", "warning"
    if due_at and as_utc_aware(due_at) < now:
        return "Reminder sent", "warning"
    return "Pending", "info"


async def _deadline_hours(tenant_id: PydanticObjectId) -> int:
    policy = await InstitutionAttendancePolicy.find_one(
        Eq(InstitutionAttendancePolicy.tenant_id, tenant_id),
        Eq(InstitutionAttendancePolicy.audience, AttendancePolicyAudience.STUDENT),
        Eq(InstitutionAttendancePolicy.is_active, True),
    )
    if policy and policy.submission_deadline_hours:
        return max(1, int(policy.submission_deadline_hours))
    return 1


async def notify_faculty_for_missing_attendance(scope: AccessScope) -> dict:
    authorize(scope, Permission.ATTENDANCE_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    today = utcnow().date()
    pending = await PendingAttendanceSubmission.find(
        Eq(PendingAttendanceSubmission.tenant_id, tenant_id),
        Eq(PendingAttendanceSubmission.status, "pending"),
        Eq(PendingAttendanceSubmission.session_date, today),
    ).to_list()
    notified = 0
    for row in pending:
        mon = await AttendanceSubmissionMonitoring.find_one(
            Eq(AttendanceSubmissionMonitoring.tenant_id, tenant_id),
            Eq(AttendanceSubmissionMonitoring.faculty_user_id, row.faculty_user_id),
            Eq(AttendanceSubmissionMonitoring.course_code, row.course_code),
            Eq(AttendanceSubmissionMonitoring.section, row.section),
            Eq(AttendanceSubmissionMonitoring.session_date, row.session_date),
        )
        if mon is None:
            mon = AttendanceSubmissionMonitoring(
                tenant_id=tenant_id,
                faculty_user_id=row.faculty_user_id,
                course_code=row.course_code,
                section=row.section,
                session_date=row.session_date,
                due_at=row.due_at,
                status="reminder_sent",
            )
            await mon.insert()
        else:
            mon.status = "reminder_sent"
            mon.snapshot_at = utcnow()
            await mon.save()
        notified += 1
    return {"notified_count": notified}


async def get_attendance_monitoring_page(
    scope: AccessScope,
    *,
    page_num: int = 1,
    page_size: int = _TABLE_LIMIT,
) -> AttendanceMonitoringPageRead:
    authorize(scope, Permission.ATTENDANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.date()
    deadline_hours = await _deadline_hours(tenant_id)

    day_start = datetime.combine(today, time.min, tzinfo=timezone.utc)
    day_end = datetime.combine(today, time.max, tzinfo=timezone.utc)

    classes_today = await ClassSession.find(
        Eq(ClassSession.tenant_id, tenant_id),
        GTE(ClassSession.scheduled_start, day_start),
        LTE(ClassSession.scheduled_start, day_end),
    ).to_list()
    scheduled = sum(1 for c in classes_today if c.status not in {"cancelled", "canceled"})

    marked = await AttendanceSession.find(
        Eq(AttendanceSession.tenant_id, tenant_id),
        Eq(AttendanceSession.session_date, today),
        Eq(AttendanceSession.status, AttendanceSessionStatus.SUBMITTED),
    ).count()

    pending_rows = await PendingAttendanceSubmission.find(
        Eq(PendingAttendanceSubmission.tenant_id, tenant_id),
        Eq(PendingAttendanceSubmission.status, "pending"),
        Eq(PendingAttendanceSubmission.session_date, today),
    ).sort("due_at").to_list()
    not_marked = len(pending_rows)

    marked_pct = round((marked / scheduled) * 100, 1) if scheduled else None

    substitutions = await DepartmentSubstituteRequest.find(
        Eq(DepartmentSubstituteRequest.tenant_id, tenant_id),
        Eq(DepartmentSubstituteRequest.session_date, today),
        In(
            DepartmentSubstituteRequest.status,
            [
                DepartmentRequestStatus.PENDING,
                DepartmentRequestStatus.APPROVED,
                DepartmentRequestStatus.COMPLETED,
            ],
        ),
    ).count()

    subs_by_class = sum(
        1 for c in classes_today if c.original_session_id is not None and c.status not in {"cancelled", "canceled"}
    )
    substitution_count = max(substitutions, subs_by_class)

    kpis = [
        UserDashboardKpi(
            key="classes_scheduled",
            label="Classes scheduled",
            value=str(scheduled),
            hint_line="Today",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="attendance_marked",
            label="Attendance marked",
            value=str(marked),
            hint_line=f"{marked_pct:g}%" if marked_pct is not None else "—",
            hint_tone="success",
        ),
        UserDashboardKpi(
            key="not_marked",
            label="Not marked",
            value=str(not_marked),
            hint_line=f"After {deadline_hours} hour" + ("s" if deadline_hours != 1 else ""),
            hint_tone="error",
        ),
        UserDashboardKpi(
            key="substitutions",
            label="Substitutions",
            value=str(substitution_count),
            hint_line="Today",
            hint_tone="muted",
        ),
    ]

    class_by_key: dict[tuple[str, str, str, date], ClassSession] = {}
    for sess in classes_today:
        key = (str(sess.faculty_user_id), (sess.course_code or "").upper(), sess.section, today)
        class_by_key[key] = sess

    faculty_ids = {r.faculty_user_id for r in pending_rows}
    users: dict[PydanticObjectId, User] = {}
    if faculty_ids:
        for user in await User.find(In(User.id, list(faculty_ids))).to_list():
            users[user.id] = user

    monitoring_rows = await AttendanceSubmissionMonitoring.find(
        Eq(AttendanceSubmissionMonitoring.tenant_id, tenant_id),
        Eq(AttendanceSubmissionMonitoring.session_date, today),
    ).to_list()
    monitoring_by_key = {
        (str(m.faculty_user_id), (m.course_code or "").upper(), m.section or "", m.session_date): m
        for m in monitoring_rows
    }

    table_rows: list[AttendanceMonitoringTableRow] = []
    for row in pending_rows:
        code = (row.course_code or "").upper()
        key = (str(row.faculty_user_id), code, row.section, row.session_date)
        class_sess = class_by_key.get(key)
        faculty = users.get(row.faculty_user_id)
        faculty_label = faculty.full_name if faculty and faculty.full_name else (faculty.email if faculty else "—")

        class_label = row.class_label.strip() if row.class_label else f"{code} - {row.section}".strip(" -")
        if class_sess and class_sess.course_code and class_sess.section:
            topic = class_sess.topic or code
            class_label = f"{topic} - {class_sess.section}"

        time_label = _format_clock(class_sess.scheduled_start) if class_sess else "—"
        if time_label == "—" and row.due_at:
            approx = as_utc_aware(row.due_at) - timedelta(hours=deadline_hours)
            time_label = approx.astimezone(_IST).strftime("%H:%M")

        room_label = (class_sess.room or class_sess.laboratory or "—") if class_sess else "—"
        anchor = class_sess.scheduled_start if class_sess else row.due_at or now
        delay_label = _delay_label(anchor, now)

        mon = monitoring_by_key.get(key)
        action_label, action_tone = _action_for(
            monitoring_status=mon.status if mon else None,
            due_at=row.due_at,
            now=now,
        )

        table_rows.append(
            AttendanceMonitoringTableRow(
                row_key=f"{key[0]}:{code}:{row.section}",
                class_label=class_label,
                faculty_label=faculty_label,
                time_label=time_label,
                room_label=room_label,
                delay_label=delay_label,
                action_label=action_label,
                action_tone=action_tone,
            ),
        )

    page_num = max(1, page_num)
    page_size = max(1, min(page_size, 50))
    total = len(table_rows)
    start = (page_num - 1) * page_size
    visible = table_rows[start : start + page_size]

    return AttendanceMonitoringPageRead(
        page_title="Attendance Monitoring",
        page_subtitle="Live view of classes today",
        notify_faculty_label="Notify faculty",
        scope_indicator_label="College scope",
        updated_at_label=_fmt_time_label(now),
        not_marked_after_label=f"After {deadline_hours} hour" + ("s" if deadline_hours != 1 else ""),
        kpis=kpis,
        not_marked_table_title="Classes not marked",
        not_marked_table_headers=["Class", "Faculty", "Time", "Room", "Delay", "Action"],
        not_marked_rows=visible,
        not_marked_table_footer_label=f"{len(visible)} of {total}",
        footer_disclaimer="Live institutional data · Attendance monitoring · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )