"""Faculty & employee overview dashboard (CA 07.01)."""

from __future__ import annotations

import math
import re
from collections import defaultdict
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In, LTE, GTE

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicYear
from app.modules.college_admin.faculty_admin_models import (
    EmployeeRecord,
    FacultyDocumentReference,
    FacultyEmploymentStatus,
    FacultyRecord,
    FacultyWorkloadRecord,
)
from app.modules.college_admin.identity_models import DepartmentKind, DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    DepartmentFacultyDesignationBar,
    FacultyEmployeeDashboardFacultyRow,
    FacultyEmployeeDashboardPageRead,
    PoliciesPagination,
    StudentAdminDashboardFilterOption,
    StudentAdminWorkQueueItem,
    UserDashboardKpi,
)
from app.modules.hr.employment_change_models import HrContractRecord, HrProbationReview
from app.modules.hr.enums import HrJobOpeningStatus, HrProbationReviewStatus, LeaveRequestStatus
from app.modules.hr.models import LeaveRequest
from app.modules.hr.enums import HrOnboardingTaskStatus
from app.modules.hr.onboarding_models import HrOnboardingProcess, HrOnboardingTask
from app.modules.hr.recruitment_models import HrJobOpening, HrJobRequisition

_IST = ZoneInfo("Asia/Kolkata")
_reader = OperationalDataReader()
_PAGE_SIZE_DEFAULT = 6
_OVERLOAD_HOURS = 20.0
_CONTRACT_WARNING_DAYS = 60

_ACTIVE_EMPLOYMENT = frozenset(
    {
        FacultyEmploymentStatus.ACTIVE,
        FacultyEmploymentStatus.CONFIRMED,
        FacultyEmploymentStatus.PROBATION,
        FacultyEmploymentStatus.AWAITING_CONFIRMATION,
        FacultyEmploymentStatus.ON_LEAVE,
    }
)

_DESIGNATION_BUCKETS: tuple[tuple[str, str], ...] = (
    ("professor", "Professor"),
    ("associate_professor", "Associate Professor"),
    ("assistant_professor", "Assistant Professor"),
    ("visiting", "Visiting / contract"),
)

_PENDING_REVIEW = frozenset(
    {
        HrProbationReviewStatus.DRAFT,
        HrProbationReviewStatus.PENDING_MANAGER,
        HrProbationReviewStatus.PENDING_HR,
        HrProbationReviewStatus.EXTENSION_RECOMMENDED,
    }
)


def _fmt_time_label(now) -> str:
    return now.astimezone(_IST).strftime("Updated %H:%M IST")


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _norm_designation(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _designation_bucket(designation: str | None, employment_type: str | None = None) -> str | None:
    blob = f"{employment_type or ''} {designation or ''}".lower()
    if any(k in blob for k in ("visiting", "adjunct", "guest", "contract faculty")):
        return "visiting"
    d = _norm_designation(designation)
    if not d:
        return None
    if "assistant professor" in d or d.startswith("asst"):
        return "assistant_professor"
    if "associate professor" in d:
        return "associate_professor"
    if re.search(r"\bprofessor\b", d) and "assistant" not in d and "associate" not in d:
        return "professor"
    return None


def _is_teaching_employee(emp: EmployeeRecord) -> bool:
    if emp.is_faculty:
        return True
    blob = f"{emp.employment_type or ''} {emp.designation or ''}".lower()
    if any(k in blob for k in ("non-teaching", "admin", "accounts", "support staff", "clerical")):
        return False
    return any(k in blob for k in ("faculty", "professor", "lecturer", "teaching", "academic"))


def _employee_active(status: FacultyEmploymentStatus) -> bool:
    return status in _ACTIVE_EMPLOYMENT


def _status_for_row(
    *,
    employment_status: FacultyEmploymentStatus,
    workload_hours: float | None,
) -> tuple[str, str]:
    if workload_hours is not None and workload_hours > _OVERLOAD_HOURS:
        return "Overloaded", "warning"
    if employment_status == FacultyEmploymentStatus.PROBATION:
        return "Probation", "info"
    if employment_status == FacultyEmploymentStatus.ON_LEAVE:
        return "On leave", "muted"
    if employment_status in (FacultyEmploymentStatus.ACTIVE, FacultyEmploymentStatus.CONFIRMED):
        return "Active", "success"
    if employment_status == FacultyEmploymentStatus.AWAITING_CONFIRMATION:
        return "Awaiting confirmation", "warning"
    return employment_status.value.replace("_", " ").title(), "muted"


def _workload_label(hours: float | None) -> str:
    if hours is None:
        return "—"
    if abs(hours - round(hours)) < 0.05:
        return f"{int(round(hours))} h"
    return f"{hours:.1f} h"


async def get_faculty_employee_dashboard_page(
    scope: AccessScope,
    *,
    academic_year_code: str | None = None,
    department_id: str | None = None,
    page: int = 1,
    page_size: int = _PAGE_SIZE_DEFAULT,
) -> FacultyEmployeeDashboardPageRead:
    authorize(scope, Permission.FACULTY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.date()

    dept_oid = to_object_id(department_id, "department_id") if department_id else None
    current_year_label, _ = await _reader.current_academic_term(tenant_id)

    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-year_code").to_list()
    selected_ay = academic_year_code or current_year_label or (years[0].year_code if years else "")
    ay_options = [StudentAdminDashboardFilterOption(value=y.year_code, label=y.label or y.year_code) for y in years]

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    dept_by_id = {d.id: d for d in departments}
    academic_dept_count = sum(1 for d in departments if d.department_kind == DepartmentKind.ACADEMIC)
    admin_unit_count = sum(1 for d in departments if d.department_kind == DepartmentKind.ADMINISTRATIVE)

    department_options = [
        StudentAdminDashboardFilterOption(value="", label="All departments"),
    ]
    for dept in sorted(departments, key=lambda d: d.name or ""):
        department_options.append(
            StudentAdminDashboardFilterOption(value=str(dept.id), label=dept.name or dept.department_code or "—"),
        )

    faculty_records = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    employee_records = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    employee_by_user = {e.user_id: e for e in employee_records}

    def faculty_matches(rec: FacultyRecord) -> bool:
        if not _employee_active(rec.employment_status):
            return False
        if dept_oid and rec.department_id != dept_oid:
            return False
        return True

    active_faculty = [r for r in faculty_records if faculty_matches(r)]
    active_faculty_users = {r.user_id for r in active_faculty}

    teaching_faculty_count = len(active_faculty)
    non_teaching_count = sum(
        1
        for emp in employee_records
        if _employee_active(emp.employment_status)
        and not emp.is_faculty
        and emp.user_id not in active_faculty_users
        and not _is_teaching_employee(emp)
        and (dept_oid is None or emp.department_id == dept_oid)
    )

    workforce_users: set[PydanticObjectId] = set(active_faculty_users)
    for emp in employee_records:
        if _employee_active(emp.employment_status) and (dept_oid is None or emp.department_id == dept_oid):
            workforce_users.add(emp.user_id)

    on_leave_today = 0
    leave_rows = await LeaveRequest.find(
        Eq(LeaveRequest.tenant_id, tenant_id),
        Eq(LeaveRequest.status, LeaveRequestStatus.APPROVED),
        LTE(LeaveRequest.start_date, today),
        GTE(LeaveRequest.end_date, today),
    ).to_list()
    on_leave_users = {req.employee_user_id for req in leave_rows if req.employee_user_id in workforce_users}
    on_leave_today = len(on_leave_users)

    openings = await HrJobOpening.find(
        Eq(HrJobOpening.tenant_id, tenant_id),
        Eq(HrJobOpening.status, HrJobOpeningStatus.PUBLISHED),
    ).to_list()
    requisition_ids = {o.requisition_id for o in openings}
    req_by_id: dict[PydanticObjectId, HrJobRequisition] = {}
    if requisition_ids:
        requisitions = await HrJobRequisition.find(
            Eq(HrJobRequisition.tenant_id, tenant_id),
            In(HrJobRequisition.id, list(requisition_ids)),
        ).to_list()
        req_by_id = {r.id: r for r in requisitions}

    vacancies = 0
    for opening in openings:
        open_slots = max(0, opening.vacancies - opening.filled_count)
        if open_slots == 0:
            continue
        if dept_oid is not None:
            req = req_by_id.get(opening.requisition_id)
            if req and req.department_id and req.department_id != dept_oid:
                continue
        vacancies += open_slots

    workload_rows = await FacultyWorkloadRecord.find(
        Eq(FacultyWorkloadRecord.tenant_id, tenant_id),
        Eq(FacultyWorkloadRecord.academic_year_label, selected_ay),
    ).to_list()
    workload_by_user: dict[PydanticObjectId, float] = {}
    for row in workload_rows:
        hours = row.total_hours or (row.lecture_hours + row.lab_hours + row.tutorial_hours)
        prev = workload_by_user.get(row.user_id)
        if prev is None or hours >= prev:
            workload_by_user[row.user_id] = hours

    user_ids = {r.user_id for r in active_faculty}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}

    table_rows: list[FacultyEmployeeDashboardFacultyRow] = []
    for rec in sorted(active_faculty, key=lambda r: (user_by_id.get(r.user_id).full_name if user_by_id.get(r.user_id) else "", str(r.id))):
        user = user_by_id.get(rec.user_id)
        emp = employee_by_user.get(rec.user_id)
        dept = dept_by_id.get(rec.department_id) if rec.department_id else None
        hours = workload_by_user.get(rec.user_id)
        status_label, status_tone = _status_for_row(employment_status=rec.employment_status, workload_hours=hours)
        emp_id = (emp.employee_id if emp and emp.employee_id else None) or rec.faculty_code or "—"
        record_id = str(rec.id)
        table_rows.append(
            FacultyEmployeeDashboardFacultyRow(
                record_id=record_id,
                faculty_name=user.full_name if user else "—",
                employee_id_label=emp_id,
                department_label=dept.name if dept else "—",
                designation_label=rec.designation or "—",
                workload_label=_workload_label(hours),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/faculty/faculty-profile?id={record_id}",
            )
        )

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total_rows = len(table_rows)
    total_pages = math.ceil(total_rows / page_size) if total_rows else 0
    start = (page - 1) * page_size
    paged_rows = table_rows[start : start + page_size]

    desig_counts: dict[str, int] = defaultdict(int)
    for rec in active_faculty:
        emp = employee_by_user.get(rec.user_id)
        bucket = _designation_bucket(rec.designation, emp.employment_type if emp else None)
        if bucket:
            desig_counts[bucket] += 1
    max_desig = max(desig_counts.values(), default=1)
    designation_bars = [
        DepartmentFacultyDesignationBar(
            key=key,
            label=label,
            value=desig_counts.get(key, 0),
            max_value=max_desig,
        )
        for key, label in _DESIGNATION_BUCKETS
    ]

    overloaded_count = sum(1 for uid, h in workload_by_user.items() if uid in active_faculty_users and h > _OVERLOAD_HOURS)

    docs = await FacultyDocumentReference.find(Eq(FacultyDocumentReference.tenant_id, tenant_id)).to_list()
    doc_pending_users = {d.user_id for d in docs if not d.authorized}
    onboarding_tasks = await HrOnboardingTask.find(
        Eq(HrOnboardingTask.tenant_id, tenant_id),
        In(
            HrOnboardingTask.status,
            [
                HrOnboardingTaskStatus.ASSIGNED,
                HrOnboardingTaskStatus.IN_PROGRESS,
                HrOnboardingTaskStatus.OVERDUE,
                HrOnboardingTaskStatus.PENDING_EMPLOYEE,
            ],
        ),
    ).to_list()
    process_ids = {t.process_id for t in onboarding_tasks if t.process_id}
    proc_by_id: dict[PydanticObjectId, HrOnboardingProcess] = {}
    if process_ids:
        processes = await HrOnboardingProcess.find(
            Eq(HrOnboardingProcess.tenant_id, tenant_id),
            In(HrOnboardingProcess.id, list(process_ids)),
        ).to_list()
        proc_by_id = {p.id: p for p in processes}
    for task in onboarding_tasks:
        if "document" in (task.title or "").lower():
            proc = proc_by_id.get(task.process_id)
            if proc and proc.employee_user_id:
                doc_pending_users.add(proc.employee_user_id)
    documents_pending_count = len(doc_pending_users)

    contract_horizon = today + timedelta(days=_CONTRACT_WARNING_DAYS)
    contracts = await HrContractRecord.find(
        Eq(HrContractRecord.tenant_id, tenant_id),
        Eq(HrContractRecord.status, "active"),
    ).to_list()
    contracts_ending_users = {
        c.employee_user_id
        for c in contracts
        if c.end_date and today <= c.end_date <= contract_horizon
    }

    probation_reviews = await HrProbationReview.find(Eq(HrProbationReview.tenant_id, tenant_id)).to_list()
    probation_due_users: set[PydanticObjectId] = set()
    for review in probation_reviews:
        if review.status in _PENDING_REVIEW:
            probation_due_users.add(review.employee_user_id)
    for rec in faculty_records:
        if rec.employment_status == FacultyEmploymentStatus.PROBATION:
            probation_due_users.add(rec.user_id)
    for emp in employee_records:
        if emp.employment_status == FacultyEmploymentStatus.PROBATION:
            probation_due_users.add(emp.user_id)

    total_employees = len(workforce_users)
    page_subtitle = (
        f"{total_employees:,} employees across {academic_dept_count} departments"
        f" and {admin_unit_count} administrative units."
    )

    kpis = [
        UserDashboardKpi(
            key="faculty",
            label="Faculty",
            value=f"{teaching_faculty_count:,}",
            hint_line="Teaching staff",
            hint_tone="neutral",
        ),
        UserDashboardKpi(
            key="non_teaching",
            label="Non-teaching staff",
            value=f"{non_teaching_count:,}",
            hint_line="Administrative and support",
            hint_tone="neutral",
        ),
        UserDashboardKpi(
            key="on_leave_today",
            label="On leave today",
            value=f"{on_leave_today:,}",
            hint_line="Approved leave",
            hint_tone="warning" if on_leave_today else "success",
        ),
        UserDashboardKpi(
            key="vacancies",
            label="Vacancies",
            value=f"{vacancies:,}",
            hint_line="Approved posts",
            hint_tone="neutral" if vacancies else "success",
        ),
    ]

    needs_attention = [
        StudentAdminWorkQueueItem(
            key="overloaded_faculty",
            title="Overloaded faculty",
            subtitle="above 20 hours",
            count=overloaded_count,
            href="/college-admin/faculty/faculty-workload-management",
            action_label="Review →",
            icon_slug="info",
        ),
        StudentAdminWorkQueueItem(
            key="documents_pending",
            title="Documents pending",
            subtitle="employees",
            count=documents_pending_count,
            href="/college-admin/faculty/employee-document-verification",
            action_label="Verify →",
            icon_slug="file-text",
        ),
        StudentAdminWorkQueueItem(
            key="contracts_ending",
            title="Contracts ending in 60 days",
            subtitle="employees",
            count=len(contracts_ending_users),
            href="/college-admin/faculty/employee-status-management",
            action_label="View →",
            icon_slug="clock",
        ),
        StudentAdminWorkQueueItem(
            key="probation_reviews",
            title="Probation reviews due",
            subtitle="reviews",
            count=len(probation_due_users),
            href="/college-admin/faculty/employee-status-management",
            action_label="Review →",
            icon_slug="calendar",
        ),
    ]

    return FacultyEmployeeDashboardPageRead(
        page_title="Faculty & Employee Dashboard",
        page_subtitle=page_subtitle,
        export_label="Export",
        add_faculty_label="+ Add faculty / employee",
        add_faculty_href="/college-admin/faculty/add-new-faculty-employee",
        academic_year_filter_label="Academic year",
        department_filter_label="Department",
        scope_indicator_label="College scope",
        updated_at_label=_fmt_time_label(now),
        academic_year_options=ay_options,
        department_options=department_options,
        selected_academic_year=selected_ay,
        selected_department_id=department_id or "",
        kpis=kpis,
        faculty_table_title="Faculty",
        faculty_table_headers=["Faculty", "ID", "Department", "Designation", "Workload", "Status"],
        faculty_rows=paged_rows,
        faculty_table_pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total_rows,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        faculty_view_all_href="/college-admin/faculty/faculty-directory",
        faculty_view_all_label="View all →",
        designation_section_title="Faculty by designation",
        designation_bars=designation_bars,
        needs_attention_title="Needs attention",
        needs_attention_items=needs_attention,
        footer_disclaimer="Live institutional data · Faculty and employee records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )