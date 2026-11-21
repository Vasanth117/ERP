"""Faculty workload management (CA 07.09)."""

from __future__ import annotations

import math
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.academics.curriculum_models import CourseRecord
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus, FacultyRecord
from app.modules.college_admin.faculty_employee_dashboard_page_service import (
    _OVERLOAD_HOURS,
    _employee_active,
    _page_numbers,
)
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    FacultyWorkloadManagementPageRead,
    FacultyWorkloadManagementTableRow,
    FacultyWorkloadRebalancePayload,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.faculty.enums import AssignmentStatus
from app.modules.faculty.models import FacultyAssignment, FacultyWorkload

_IST = ZoneInfo("Asia/Kolkata")
_reader = OperationalDataReader()
_PAGE_SIZE = 4
_POLICY_TARGET = 16.0
_UNDERLOAD_HOURS = 12.0


def _policy_hours(designation: str | None) -> float:
    blob = (designation or "").lower()
    if "assistant" in blob or "lecturer" in blob:
        return 16.0
    return 20.0


def _workload_status(total: float, policy: float) -> tuple[str, str]:
    if total > _OVERLOAD_HOURS:
        return "Overloaded", "warning"
    if total < _UNDERLOAD_HOURS:
        return "Under", "info"
    if total <= policy:
        return "Within", "success"
    return "Within", "success"


def _is_lab_course(name: str | None, code: str | None) -> bool:
    blob = f"{name or ''} {code or ''}".lower()
    return any(k in blob for k in ("lab", "laboratory", "practical", "workshop"))


async def _hours_from_assignments(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    year_label: str,
    semester_label: str,
) -> tuple[float, float, float]:
    assignments = await FacultyAssignment.find(
        Eq(FacultyAssignment.tenant_id, tenant_id),
        Eq(FacultyAssignment.user_id, user_id),
        Eq(FacultyAssignment.academic_year_label, year_label),
        Eq(FacultyAssignment.semester_label, semester_label),
        Eq(FacultyAssignment.status, AssignmentStatus.ACTIVE),
    ).to_list()
    courses = await CourseRecord.find(Eq(CourseRecord.tenant_id, tenant_id)).to_list()
    course_by_code = {c.course_code: c for c in courses}
    theory = 0.0
    lab = 0.0
    for item in assignments:
        course = course_by_code.get(item.course_code)
        if course:
            theory += float(course.lecture_hours + course.tutorial_hours)
            lab += float(course.practical_hours)
        elif _is_lab_course(item.course_name, item.course_code):
            lab += 3.0
        else:
            theory += 3.0
    total = theory + lab
    return theory, lab, total


async def _resolve_hours(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    year_label: str,
    semester_label: str,
) -> tuple[float, float, float]:
    workload = await FacultyWorkload.find_one(
        Eq(FacultyWorkload.tenant_id, tenant_id),
        Eq(FacultyWorkload.user_id, user_id),
        Eq(FacultyWorkload.academic_year_label, year_label),
        Eq(FacultyWorkload.semester_label, semester_label),
    )
    if workload and workload.total_hours > 0:
        return workload.lecture_hours, workload.lab_hours, workload.total_hours
    return await _hours_from_assignments(tenant_id, user_id, year_label=year_label, semester_label=semester_label)


async def _rebalance_workloads(
    scope: AccessScope,
    *,
    year_label: str,
    semester_label: str,
) -> None:
    authorize(scope, Permission.FACULTY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    faculty = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    for record in faculty:
        if not _employee_active(record.employment_status):
            continue
        theory, lab, total = await _hours_from_assignments(
            tenant_id,
            record.user_id,
            year_label=year_label,
            semester_label=semester_label,
        )
        workload = await FacultyWorkload.find_one(
            Eq(FacultyWorkload.tenant_id, tenant_id),
            Eq(FacultyWorkload.user_id, record.user_id),
            Eq(FacultyWorkload.academic_year_label, year_label),
            Eq(FacultyWorkload.semester_label, semester_label),
        )
        if workload is None:
            workload = FacultyWorkload(
                tenant_id=tenant_id,
                user_id=record.user_id,
                academic_year_label=year_label,
                semester_label=semester_label,
            )
        workload.lecture_hours = theory
        workload.lab_hours = lab
        workload.total_hours = total
        workload.computed_at = utcnow()
        if workload.id is None:
            await workload.insert()
        else:
            await workload.save()


async def get_faculty_workload_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> FacultyWorkloadManagementPageRead:
    authorize(scope, Permission.FACULTY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    year_label, sem_label = await _reader.current_academic_term(tenant_id)
    selected_year = academic_year_label or year_label or "2026–27"
    selected_semester = semester_label or sem_label or "Odd"

    faculty = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    active = [r for r in faculty if _employee_active(r.employment_status)]
    departments = await InstitutionDepartment.find(Eq(InstitutionDepartment.tenant_id, tenant_id)).to_list()
    dept_by_id = {d.id: d for d in departments}

    rows_data: list[tuple[FacultyRecord, User, float, float, float, float]] = []
    totals: list[float] = []
    overloaded = 0
    underloaded = 0
    within = 0

    for record in active:
        user = await User.get(record.user_id)
        if user is None:
            continue
        theory, lab, total = await _resolve_hours(
            tenant_id,
            record.user_id,
            year_label=selected_year,
            semester_label=selected_semester,
        )
        policy = _policy_hours(record.designation)
        status_label, _ = _workload_status(total, policy)
        if status_label == "Overloaded":
            overloaded += 1
        elif status_label == "Under":
            underloaded += 1
        else:
            within += 1
        totals.append(total)
        rows_data.append((record, user, theory, lab, total, policy))

    rows_data.sort(key=lambda r: (-r[4], r[1].full_name.lower()))

    total_count = len(rows_data)
    total_pages = max(1, math.ceil(total_count / _PAGE_SIZE)) if total_count else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_slice = rows_data[start : start + _PAGE_SIZE]

    table_rows: list[FacultyWorkloadManagementTableRow] = []
    for record, user, theory, lab, total, policy in page_slice:
        dept = dept_by_id.get(record.department_id) if record.department_id else None
        dept_label = dept.name if dept else "—"
        status_label, status_tone = _workload_status(total, policy)
        record_id = str(record.id)
        table_rows.append(
            FacultyWorkloadManagementTableRow(
                record_id=record_id,
                faculty_name=user.full_name,
                department_label=dept_label,
                theory_hours_label=str(int(round(theory))),
                lab_hours_label=str(int(round(lab))),
                total_hours_label=f"{int(round(total))} h",
                policy_hours_label=f"{int(policy)} h",
                status_label=status_label,
                status_tone=status_tone,
                timetable_href=f"/college-admin/faculty/faculty-timetable?id={record_id}",
            )
        )

    avg = sum(totals) / len(totals) if totals else 0.0
    kpis = [
        UserDashboardKpi(
            key="average_load",
            label="Average load",
            value=f"{avg:.1f} h",
            hint_line=f"Policy {_POLICY_TARGET:.0f} h",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="overloaded",
            label="Overloaded",
            value=str(overloaded),
            hint_line=f"Above {int(_OVERLOAD_HOURS)} h",
            hint_tone="warning",
        ),
        UserDashboardKpi(
            key="underloaded",
            label="Under-loaded",
            value=str(underloaded),
            hint_line=f"Below {int(_UNDERLOAD_HOURS)} h",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="within_policy",
            label="Within policy",
            value=str(within),
            hint_line="Teaching load OK",
            hint_tone="success",
        ),
    ]

    showing = f"Showing {len(table_rows)} of {total_count}" if total_count else "Showing 0 of 0"
    pagination = PoliciesPagination(
        page=page,
        page_size=_PAGE_SIZE,
        total=total_count,
        total_pages=total_pages,
        page_numbers=_page_numbers(total_pages),
        has_previous=page > 1,
        has_next=page < total_pages if total_pages else False,
    )

    return FacultyWorkloadManagementPageRead(
        page_title="Faculty Workload Management",
        page_subtitle="Teaching load against policy",
        export_label="Export",
        rebalance_label="Rebalance",
        workload_section_title="Workload",
        table_headers=["Faculty", "Department", "Theory", "Lab", "Total", "Policy", "Status"],
        workload_rows=table_rows,
        showing_label=showing,
        pagination=pagination,
        kpis=kpis,
        selected_academic_year=selected_year,
        selected_semester_label=selected_semester,
        footer_disclaimer="Live institutional data · Faculty and employee records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def rebalance_faculty_workload_page(
    scope: AccessScope,
    payload: FacultyWorkloadRebalancePayload,
) -> FacultyWorkloadManagementPageRead:
    tenant_id = require_college_tenant_scope(scope)
    year_label, sem_label = await _reader.current_academic_term(tenant_id)
    selected_year = payload.academic_year_label or year_label or "2026–27"
    selected_semester = payload.semester_label or sem_label or "Odd"
    if not selected_year or not selected_semester:
        raise AppError(code="VALIDATION_ERROR", message="Academic year and semester are required", status_code=422)
    await _rebalance_workloads(scope, year_label=selected_year, semester_label=selected_semester)
    return await get_faculty_workload_management_page(
        scope,
        page=1,
        academic_year_label=selected_year,
        semester_label=selected_semester,
    )