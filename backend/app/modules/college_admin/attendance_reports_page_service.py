"""Attendance reports catalogue page (CA 08.12)."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.academic_config_models import AcademicYear
from app.modules.college_admin.attendance_admin_models import AttendanceReportDefinition, AttendanceReportExecution
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AttendanceReportCreate,
    AttendanceReportsPageRead,
    AttendanceReportsTableRow,
    InstitutionFieldOption,
)

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 4

_CREATE_TEMPLATES = [
    InstitutionFieldOption(value="custom_summary", label="Department attendance summary"),
    InstitutionFieldOption(value="custom_shortage", label="Shortage list"),
    InstitutionFieldOption(value="custom_faculty", label="Faculty attendance"),
    InstitutionFieldOption(value="custom_subject", label="Subject-wise attendance"),
    InstitutionFieldOption(value="custom_compliance", label="Compliance snapshot"),
]

_BUILTIN_SEED: list[tuple[str, str, list[str], str, int]] = [
    ("dept_summary", "Department attendance summary", ["PDF", "Excel"], "Weekly", 0),
    ("shortage_list", "Shortage list", ["PDF", "CSV"], "Daily", 1),
    ("faculty_attendance", "Faculty attendance", ["Excel"], "Monthly", 2),
    ("subject_wise", "Subject-wise attendance", ["CSV"], "On demand", 3),
    ("compliance_snapshot", "Compliance snapshot", ["PDF"], "Monthly", 4),
    ("correction_summary", "Correction requests summary", ["PDF", "Excel"], "Weekly", 5),
    ("monitoring_daily", "Monitoring daily digest", ["PDF"], "Daily", 6),
    ("session_history", "Session submission history", ["Excel", "CSV"], "Weekly", 7),
    ("student_shortage", "Student shortage notices", ["PDF", "CSV"], "On demand", 8),
]

_VALID_TEMPLATES = {t.value for t in _CREATE_TEMPLATES}


def _fmt_snapshot(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Sample snapshot · %d %b %Y, %H:%M IST")


def _fmt_last_run(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return as_utc_aware(dt).astimezone(_IST).strftime("%d %b")


def _format_labels(formats: list[str]) -> str:
    return ", ".join(formats) if formats else "—"


async def _academic_period_labels(tenant_id: PydanticObjectId) -> tuple[str, str]:
    now = utcnow().astimezone(_IST)
    month_label = now.strftime("%b %Y")
    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-start_date").to_list()
    current = next((y for y in years if y.is_current), years[0] if years else None)
    if current and current.label:
        semester = "Odd" if now.month in (7, 8, 9, 10, 11, 12, 1) else "Even"
        label = current.label.replace("-", "–")
        term_label = f"{semester} {label}"
    else:
        term_label = f"Odd {now.year}–{(now.year + 1) % 100:02d}"
    return month_label, term_label


async def _ensure_reports(tenant_id: PydanticObjectId) -> list[AttendanceReportDefinition]:
    rows = await AttendanceReportDefinition.find(
        Eq(AttendanceReportDefinition.tenant_id, tenant_id),
        Eq(AttendanceReportDefinition.is_active, True),
    ).sort("sort_order").to_list()
    if rows:
        return rows

    month_label, term_label = await _academic_period_labels(tenant_id)
    now = utcnow()
    period_for = {
        "dept_summary": month_label,
        "shortage_list": term_label,
        "faculty_attendance": month_label,
        "subject_wise": term_label,
        "compliance_snapshot": term_label,
        "correction_summary": month_label,
        "monitoring_daily": month_label,
        "session_history": term_label,
        "student_shortage": term_label,
    }
    last_run_offsets = [0, 0, 1, 3, 5, 4, 2, 6, 7]
    created: list[AttendanceReportDefinition] = []
    for index, (key, title, formats, schedule, order) in enumerate(_BUILTIN_SEED):
        last_run = now - timedelta(days=last_run_offsets[index] if index < len(last_run_offsets) else 0)
        doc = AttendanceReportDefinition(
            tenant_id=tenant_id,
            report_key=key,
            title=title,
            period_label=period_for.get(key, month_label),
            export_formats=formats,
            schedule_label=schedule,
            last_run_at=last_run,
            sort_order=order,
            is_builtin=True,
        )
        await doc.insert()
        await AttendanceReportExecution(
            tenant_id=tenant_id,
            report_key=key,
            period_label=doc.period_label,
            run_at=last_run,
        ).insert()
        created.append(doc)
    return created


async def _refresh_periods(tenant_id: PydanticObjectId, rows: list[AttendanceReportDefinition]) -> None:
    month_label, term_label = await _academic_period_labels(tenant_id)
    term_keys = {
        "shortage_list",
        "subject_wise",
        "compliance_snapshot",
        "session_history",
        "student_shortage",
    }
    changed = False
    for row in rows:
        target = term_label if row.report_key in term_keys else month_label
        if row.period_label != target:
            row.period_label = target
            row.updated_at = utcnow()
            changed = True
    if changed:
        for row in rows:
            await row.save()


async def get_attendance_reports_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> AttendanceReportsPageRead:
    authorize(scope, Permission.ATTENDANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    rows = await _ensure_reports(tenant_id)
    await _refresh_periods(tenant_id, rows)

    page = max(1, page)
    page_size = max(1, min(page_size, 20))
    total = len(rows)
    start = (page - 1) * page_size
    visible = rows[start : start + page_size]

    table_rows: list[AttendanceReportsTableRow] = []
    for row in visible:
        table_rows.append(
            AttendanceReportsTableRow(
                row_key=row.report_key,
                report_title=row.title,
                period_label=row.period_label,
                format_label=_format_labels(row.export_formats),
                last_run_label=_fmt_last_run(row.last_run_at),
                schedule_label=row.schedule_label,
            ),
        )

    return AttendanceReportsPageRead(
        page_title="Attendance Reports",
        page_subtitle="Standard and scheduled reports",
        create_report_label="Create report",
        reports_section_title="Reports",
        reports_table_headers=["Report", "Period", "Format", "Last run", "Schedule"],
        report_rows=table_rows,
        reports_table_footer_label=f"{len(table_rows)} of {total} reports",
        create_report_templates=_CREATE_TEMPLATES,
        footer_disclaimer="Illustrative data only · No live student, faculty or finance records · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )


async def create_attendance_report(scope: AccessScope, payload: AttendanceReportCreate) -> AttendanceReportsPageRead:
    authorize(scope, Permission.ATTENDANCE_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    if payload.template_key not in _VALID_TEMPLATES:
        raise AppError(code="VALIDATION_ERROR", message="Unknown report template", status_code=422)

    template = next(t for t in _CREATE_TEMPLATES if t.value == payload.template_key)
    title = (payload.title or template.label).strip()
    suffix = int(utcnow().timestamp()) % 10000
    report_key = f"{payload.template_key}_{suffix}"

    existing = await AttendanceReportDefinition.find_one(
        Eq(AttendanceReportDefinition.tenant_id, tenant_id),
        Eq(AttendanceReportDefinition.report_key, report_key),
    )
    if existing:
        report_key = f"{payload.template_key}_{suffix + 1}"

    month_label, term_label = await _academic_period_labels(tenant_id)
    period = term_label if "shortage" in payload.template_key or "subject" in payload.template_key else month_label
    now = utcnow()

    formats = ["PDF", "CSV"]
    if "faculty" in payload.template_key:
        formats = ["Excel"]
    if "compliance" in payload.template_key:
        formats = ["PDF"]

    doc = AttendanceReportDefinition(
        tenant_id=tenant_id,
        report_key=report_key,
        title=title,
        period_label=period,
        export_formats=formats,
        schedule_label="On demand",
        last_run_at=now,
        sort_order=100 + suffix,
        is_builtin=False,
    )
    await doc.insert()
    await AttendanceReportExecution(
        tenant_id=tenant_id,
        report_key=report_key,
        period_label=period,
        run_at=now,
        run_by=scope.user_id,
    ).insert()

    from app.modules.audit.service import record_audit

    await record_audit(
        actor_id=scope.user_id,
        action="college.attendance.report_created",
        resource_type="attendance_report_definition",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        metadata={"report_key": report_key, "template_key": payload.template_key},
    )
    return await get_attendance_reports_page(scope)