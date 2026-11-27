"""Academic reports module pages (CA 16.02–06)."""

from __future__ import annotations

import math
from calendar import month_name
from datetime import datetime
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.academics.curriculum_models import SectionOffering
from app.modules.college_admin.academic_config_models import AcademicProgramme, AcademicYear
from app.modules.college_admin.attendance_overview_service import get_attendance_overview
from app.modules.college_admin.enums import DashboardDateRange
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.reports_academic_catalog import page_meta, page_rows
from app.modules.college_admin.reports_admin_models import (
    InstitutionReportsAcademicDefinition,
    InstitutionReportJob,
    ReportJobStatus,
)
from app.modules.college_admin.schemas import (
    InstitutionFieldOption,
    PoliciesPagination,
    ReportsAcademicHighlightBar,
    ReportsAcademicModulePageRead,
    ReportsAcademicTableRow,
    UserDashboardKpi,
)
from app.modules.college_admin.student_admin_models import (
    StudentAdmission,
    StudentLifecycleStatus,
    StudentRecord,
    StudentTransfer,
    TransferStatus,
)
from app.modules.students.models import StudentProfile
from app.modules.college_admin.workflow_admin_models import ApprovalTaskStatus, InstitutionApprovalTask

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 4
_TABLE_HEADERS = ["Report", "Period", "Format", "Last run", "Schedule"]
_HIGHLIGHT_TONES = ("success", "success", "info", "warning")
_FORMAT_LABELS = {"csv": "CSV", "excel": "Excel", "pdf": "PDF", "xlsx": "Excel"}

_reader = OperationalDataReader()


def _fmt_updated(now: datetime) -> str:
    return f"● Updated {now.astimezone(_IST).strftime('%H:%M')} IST"


def _fmt_last_run(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return as_utc_aware(dt).astimezone(_IST).strftime("%d %b")


def _format_labels(formats: list[str]) -> str:
    labels: list[str] = []
    for fmt in formats:
        key = (fmt or "").lower()
        label = _FORMAT_LABELS.get(key, key.upper())
        if label not in labels:
            labels.append(label)
    return ", ".join(labels) if labels else "—"


async def _academic_year_label(tenant_id: PydanticObjectId, academic_year: str | None) -> str:
    if academic_year:
        return academic_year.replace("-", "–")
    year, _ = await _reader.current_academic_term(tenant_id)
    if year:
        return year.replace("-", "–")
    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-start_date").to_list()
    current = next((y for y in years if y.is_current), years[0] if years else None)
    if current and current.label:
        return current.label.replace("-", "–")
    now = utcnow().astimezone(_IST)
    return f"{now.year}–{(now.year + 1) % 100:02d}"


async def _period_for(kind: str, tenant_id: PydanticObjectId, ay_label: str) -> str:
    now = utcnow().astimezone(_IST)
    if kind == "year":
        return f"AY {ay_label}"
    if kind == "term":
        semester = "Odd" if now.month in (7, 8, 9, 10, 11, 12, 1) else "Even"
        return f"{semester} {ay_label.split('–')[0] if '–' in ay_label else now.year}"
    if kind == "on_demand":
        return "—"
    return f"{month_name[now.month][:3]} {now.year}"


async def _ensure_definitions(
    tenant_id: PydanticObjectId,
    page_key: str,
    ay_label: str,
) -> list[InstitutionReportsAcademicDefinition]:
    existing = await InstitutionReportsAcademicDefinition.find(
        Eq(InstitutionReportsAcademicDefinition.tenant_id, tenant_id),
        Eq(InstitutionReportsAcademicDefinition.page_key, page_key),
        Eq(InstitutionReportsAcademicDefinition.is_active, True),
    ).sort("+sort_order").to_list()
    if existing:
        changed = False
        for row in existing:
            period = await _period_for("month", tenant_id, ay_label)
            if row.report_key in {s.report_key for s in page_rows(page_key) if s.period_kind == "year"}:
                period = await _period_for("year", tenant_id, ay_label)
            seed = next((s for s in page_rows(page_key) if s.report_key == row.report_key), None)
            if seed:
                period = await _period_for(seed.period_kind, tenant_id, ay_label)
            if row.period_label != period:
                row.period_label = period
                row.updated_at = utcnow()
                changed = True
        if changed:
            for row in existing:
                await row.save()
        return existing

    seeds = page_rows(page_key)
    created: list[InstitutionReportsAcademicDefinition] = []
    now = utcnow()
    for index, seed in enumerate(seeds):
        period = await _period_for(seed.period_kind, tenant_id, ay_label)
        doc = InstitutionReportsAcademicDefinition(
            tenant_id=tenant_id,
            page_key=page_key,
            report_key=seed.report_key,
            title=seed.title,
            period_label=period,
            export_formats=list(seed.export_formats),
            schedule_label=seed.schedule_label,
            last_run_at=None,
            sort_order=index,
        )
        await doc.insert()
        created.append(doc)
    return created


async def _sync_last_runs(
    tenant_id: PydanticObjectId,
    definitions: list[InstitutionReportsAcademicDefinition],
    meta_run_key: str,
) -> None:
    jobs = await InstitutionReportJob.find(
        Eq(InstitutionReportJob.tenant_id, tenant_id),
        Eq(InstitutionReportJob.report_key, meta_run_key),
        Eq(InstitutionReportJob.status, ReportJobStatus.COMPLETED),
    ).sort("-completed_at").to_list()
    latest = jobs[0] if jobs else None
    if not latest:
        return
    completed = latest.completed_at or latest.created_at
    for definition in definitions[:4]:
        if definition.last_run_at is None:
            definition.last_run_at = completed
            definition.updated_at = utcnow()
            await definition.save()


async def _department_options(tenant_id: PydanticObjectId) -> list[InstitutionFieldOption]:
    depts = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).sort("+name").to_list()
    options = [InstitutionFieldOption(value="", label="All departments")]
    for dept in depts:
        options.append(InstitutionFieldOption(value=str(dept.id), label=dept.name or dept.code or str(dept.id)))
    return options


async def _department_highlights(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    *,
    department_id: PydanticObjectId | None,
    mode: str,
) -> list[ReportsAcademicHighlightBar]:
    depts = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    if department_id:
        depts = [d for d in depts if d.id == department_id]
    if not depts:
        return []

    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    counts: dict[PydanticObjectId, int] = {}
    for profile in profiles:
        if profile.department_id:
            counts[profile.department_id] = counts.get(profile.department_id, 0) + 1

    dept_metrics: list[tuple[InstitutionDepartment, float]] = []
    if mode == "attendance":
        overview = await get_attendance_overview(
            scope,
            date_range=DashboardDateRange.SEMESTER,
            department_id=str(department_id) if department_id else None,
        )
        for row in overview.department_rows:
            dept = next((d for d in depts if str(d.id) == row.department_id), None)
            if dept and row.semester_avg_pct is not None:
                dept_metrics.append((dept, float(row.semester_avg_pct)))
    else:
        max_count = max(counts.values()) if counts else 1
        for dept in depts:
            cnt = counts.get(dept.id, 0)
            pct = round((cnt / max_count) * 100) if max_count else 0
            dept_metrics.append((dept, float(min(100, pct))))

    dept_metrics.sort(key=lambda item: item[1], reverse=True)
    bars: list[ReportsAcademicHighlightBar] = []
    for index, (dept, value) in enumerate(dept_metrics[:4]):
        bars.append(
            ReportsAcademicHighlightBar(
                bar_key=str(dept.id),
                department_label=dept.name or dept.code or "Department",
                percent_value=int(round(value)),
                tone=_HIGHLIGHT_TONES[index % len(_HIGHLIGHT_TONES)],
            )
        )
    return bars


async def _student_kpis(
    tenant_id: PydanticObjectId,
    department_id: PydanticObjectId | None,
    ay_label: str,
) -> list[UserDashboardKpi]:
    if department_id:
        students = await StudentRecord.find(
            Eq(StudentRecord.tenant_id, tenant_id),
            Eq(StudentRecord.department_id, department_id),
        ).to_list()
    else:
        students = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).to_list()
    active = sum(
        1
        for s in students
        if s.lifecycle_status in (StudentLifecycleStatus.ACTIVE, StudentLifecycleStatus.ADMITTED, StudentLifecycleStatus.ON_LEAVE)
    )
    admissions = await StudentAdmission.find(Eq(StudentAdmission.tenant_id, tenant_id)).to_list()
    new_adm = len(admissions)
    transfers = await StudentTransfer.find(
        Eq(StudentTransfer.tenant_id, tenant_id),
        In(StudentTransfer.status, [TransferStatus.APPROVED, TransferStatus.COMPLETED]),
    ).count()
    dropouts = sum(
        1
        for s in students
        if s.lifecycle_status in (StudentLifecycleStatus.WITHDRAWN, StudentLifecycleStatus.DISCONTINUED)
    )
    headcount = await _reader.headcount_statistics(tenant_id, department_id=department_id)
    total = headcount.total_students or active or len(students)
    return [
        UserDashboardKpi(key="students", label="Students", value=f"{total:,}", hint_line="", hint_tone="info"),
        UserDashboardKpi(
            key="admissions",
            label="New admissions",
            value=f"{new_adm:,}",
            hint_line=f"AY {ay_label}",
            hint_tone="success",
        ),
        UserDashboardKpi(key="transfers", label="Transfers", value=f"{transfers:,}", hint_line="", hint_tone="info"),
        UserDashboardKpi(key="dropouts", label="Dropouts", value=f"{dropouts:,}", hint_line="", hint_tone="warning"),
    ]


async def _department_kpis(tenant_id: PydanticObjectId, department_id: PydanticObjectId | None) -> list[UserDashboardKpi]:
    headcount = await _reader.headcount_statistics(tenant_id, department_id=department_id)
    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).count()
    sections = await SectionOffering.find(Eq(SectionOffering.tenant_id, tenant_id)).count()
    pending = await InstitutionApprovalTask.find(
        Eq(InstitutionApprovalTask.tenant_id, tenant_id),
        Eq(InstitutionApprovalTask.status, ApprovalTaskStatus.PENDING),
    ).count()
    return [
        UserDashboardKpi(key="departments", label="Departments", value=f"{headcount.department_count:,}", hint_line="", hint_tone="info"),
        UserDashboardKpi(key="programmes", label="Programmes", value=f"{programmes or headcount.programme_count:,}", hint_line="", hint_tone="info"),
        UserDashboardKpi(key="sections", label="Sections", value=f"{sections:,}", hint_line="", hint_tone="info"),
        UserDashboardKpi(
            key="hod_pending",
            label="Pending HOD actions",
            value=f"{pending:,}",
            hint_line="",
            hint_tone="warning" if pending else "success",
        ),
    ]


async def _performance_kpis(scope: AccessScope, tenant_id: PydanticObjectId, ay_label: str) -> list[UserDashboardKpi]:
    from app.modules.college_admin.academic_performance_overview_service import get_academic_performance_overview
    from app.modules.college_admin.reports_admin_service import _permission_allowed

    if not _permission_allowed(scope, Permission.COLLEGE_DASHBOARD_READ.value):
        return [
            UserDashboardKpi(key="pass_pct", label="Pass percentage", value="—", hint_line="Last semester", hint_tone="muted"),
            UserDashboardKpi(key="avg_cgpa", label="Average CGPA", value="—", hint_line="", hint_tone="muted"),
            UserDashboardKpi(key="backlogs", label="Backlogs", value="—", hint_line="", hint_tone="muted"),
            UserDashboardKpi(key="distinction", label="Distinction", value="—", hint_line="", hint_tone="muted"),
        ]
    overview = await get_academic_performance_overview(scope, academic_year_label=ay_label.replace("–", "-"))
    k = overview.kpis
    return [
        UserDashboardKpi(
            key="pass_pct",
            label="Pass percentage",
            value=f"{k.overall_pass_rate_pct:.1f}%" if k.overall_pass_rate_pct is not None else "—",
            hint_line="Last semester",
            hint_tone="success",
        ),
        UserDashboardKpi(
            key="avg_cgpa",
            label="Average CGPA",
            value=f"{k.average_cgpa:.2f}" if k.average_cgpa is not None else "—",
            hint_line="",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="backlogs",
            label="Backlogs",
            value=f"{k.students_with_backlogs:,}",
            hint_line="",
            hint_tone="warning",
        ),
        UserDashboardKpi(
            key="distinction",
            label="Distinction",
            value=f"{k.first_class_distinction_pct:.1f}%" if k.first_class_distinction_pct is not None else "—",
            hint_line="",
            hint_tone="success",
        ),
    ]


async def _attendance_kpis(scope: AccessScope, department_id: PydanticObjectId | None) -> list[UserDashboardKpi]:
    overview = await get_attendance_overview(
        scope,
        date_range=DashboardDateRange.MONTH,
        department_id=str(department_id) if department_id else None,
    )
    k = overview.kpis
    return [
        UserDashboardKpi(
            key="avg_attendance",
            label="Average attendance",
            value=f"{k.semester_average_pct:.1f}%" if k.semester_average_pct is not None else "—",
            hint_line="",
            hint_tone="success",
        ),
        UserDashboardKpi(
            key="below_min",
            label="Below 75%",
            value=f"{k.students_below_minimum:,}",
            hint_line="Students",
            hint_tone="error" if k.students_below_minimum else "success",
        ),
        UserDashboardKpi(
            key="faculty_present",
            label="Faculty present",
            value=f"{k.today_faculty_attendance_pct:.1f}%" if k.today_faculty_attendance_pct is not None else "—",
            hint_line="",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="corrections",
            label="Corrections",
            value=f"{sum(bucket.count for bucket in overview.correction_requests):,}",
            hint_line="Pending",
            hint_tone="warning",
        ),
    ]


async def _examination_kpis(tenant_id: PydanticObjectId, ay_label: str) -> list[UserDashboardKpi]:
    year, semester = await _reader.current_academic_term(tenant_id)
    year = year or ay_label.replace("–", "-").split("–")[0]
    summary = await _reader.examination_summary(tenant_id, academic_year_label=year, semester_label=semester)
    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).count()
    registered = profiles
    eligible = max(registered - summary.pending_evaluations, 0)
    return [
        UserDashboardKpi(
            key="registered",
            label="Registered",
            value=f"{registered:,}",
            hint_line=f"{round((registered / profiles) * 100, 1) if profiles else 0}%",
            hint_tone="success",
        ),
        UserDashboardKpi(key="eligible", label="Eligible", value=f"{eligible:,}", hint_line="", hint_tone="info"),
        UserDashboardKpi(
            key="revaluation",
            label="Revaluation requests",
            value=f"{summary.pending_evaluations:,}",
            hint_line="",
            hint_tone="warning",
        ),
        UserDashboardKpi(
            key="supplementary",
            label="Supplementary",
            value=f"{max(summary.scheduled_exams // 4, 0):,}",
            hint_line="",
            hint_tone="info",
        ),
    ]


async def _kpis_for_page(
    page_key: str,
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    department_id: PydanticObjectId | None,
    ay_label: str,
) -> list[UserDashboardKpi]:
    if page_key == "student":
        return await _student_kpis(tenant_id, department_id, ay_label)
    if page_key == "department":
        return await _department_kpis(tenant_id, department_id)
    if page_key == "academic-performance":
        return await _performance_kpis(scope, tenant_id, ay_label)
    if page_key == "attendance":
        return await _attendance_kpis(scope, department_id)
    if page_key == "examination":
        return await _examination_kpis(tenant_id, ay_label)
    return []


def _highlight_mode(page_key: str) -> str:
    return "attendance" if page_key == "attendance" else "enrollment"


async def get_reports_academic_module_page(
    scope: AccessScope,
    *,
    page_key: str,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
    academic_year: str | None = None,
    department_id: str | None = None,
) -> ReportsAcademicModulePageRead:
    meta = page_meta(page_key)
    if meta is None:
        raise AppError(code="NOT_FOUND", message="Unknown reports page", status_code=404)
    authorize(scope, meta.permission)
    tenant_id = require_college_tenant_scope(scope)
    dept_oid = to_object_id(department_id, "department_id") if department_id else None
    now = utcnow()
    ay_label = await _academic_year_label(tenant_id, academic_year)

    definitions = await _ensure_definitions(tenant_id, page_key, ay_label)
    await _sync_last_runs(tenant_id, definitions, meta.run_report_key)

    total = len(definitions)
    page = max(1, page)
    page_size = max(1, min(page_size, 20))
    start = (page - 1) * page_size
    visible = definitions[start : start + page_size]

    table_rows = [
        ReportsAcademicTableRow(
            row_key=row.report_key,
            report_label=row.title,
            period_label=row.period_label,
            format_label=_format_labels(row.export_formats),
            last_run_label=_fmt_last_run(row.last_run_at),
            schedule_label=row.schedule_label,
        )
        for row in visible
    ]

    kpis = await _kpis_for_page(page_key, scope, tenant_id, dept_oid, ay_label)
    highlights = await _department_highlights(
        scope,
        tenant_id,
        department_id=dept_oid,
        mode=_highlight_mode(page_key),
    )

    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, start + len(table_rows))

    return ReportsAcademicModulePageRead(
        page_key=page_key,
        page_title=meta.page_title,
        page_subtitle=meta.page_subtitle,
        export_label="Export",
        run_report_label="Run report",
        academic_year_label=f"AY {ay_label}",
        academic_year_options=[
            InstitutionFieldOption(value=ay_label, label=f"AY {ay_label}"),
        ],
        department_filter_label="All departments",
        department_options=await _department_options(tenant_id),
        selected_department_id=department_id or "",
        scope_badge_label="College scope" if not dept_oid else "Department scope",
        updated_at_label=_fmt_updated(now),
        kpis=kpis,
        reports_section_title="Reports",
        highlights_section_title="Highlights",
        table_headers=_TABLE_HEADERS,
        report_rows=table_rows,
        highlight_bars=highlights,
        empty_table_message="No reports configured yet.",
        empty_highlights_message="No department highlights yet.",
        showing_label=f"Showing {showing_end} of {total}",
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        run_report_key=meta.run_report_key,
        generated_at=now,
    )