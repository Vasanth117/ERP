"""Faculty subject allocation (CA 07.08)."""

from __future__ import annotations

from collections import defaultdict
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.academics.curriculum_models import CourseRecord
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicYear
from app.modules.college_admin.faculty_admin_models import FacultyRecord
from app.modules.college_admin.faculty_admin_service import assign_teaching
from app.modules.college_admin.faculty_admin_schemas import TeachingAssignmentCreate
from app.modules.college_admin.faculty_employee_dashboard_page_service import _OVERLOAD_HOURS
from app.modules.college_admin.identity_models import DepartmentKind, DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    FacultyAssignmentWorkflowStep,
    FacultySubjectAllocationConfirmPayload,
    FacultySubjectAllocationFilterPayload,
    FacultySubjectAllocationPageRead,
    FacultySubjectAllocationTableRow,
    FacultySubjectCapacityRow,
    StudentAdminDashboardFilterOption,
)
from app.modules.faculty.enums import AssignmentStatus
from app.modules.faculty.models import FacultyAssignment, FacultyWorkload

_IST = ZoneInfo("Asia/Kolkata")
_reader = OperationalDataReader()
_SUBJECT_PREVIEW = 22

_SEMESTER_OPTIONS = ("Odd", "Even")


def _fmt_time_label(now) -> str:
    return now.astimezone(_IST).strftime("Updated %H:%M IST")


def _course_hours(course: CourseRecord) -> float:
    return float(course.lecture_hours + course.tutorial_hours + course.practical_hours) or float(
        max(course.credit_units * 2, 1)
    )


def _load_tone(assigned: float, capacity: float) -> str:
    if capacity <= 0:
        return "muted"
    ratio = assigned / capacity
    if ratio >= 0.9:
        return "warning"
    if ratio >= 0.7:
        return "info"
    return "success"


def _workflow_steps(active_key: str = "subject_allocation") -> list[FacultyAssignmentWorkflowStep]:
    steps_def = [
        ("faculty_directory", "Faculty directory", 1, "/college-admin/faculty/faculty-directory"),
        ("faculty_profile", "Faculty profile", 2, "/college-admin/faculty/faculty-profile"),
        ("subject_allocation", "Subject allocation", 3, "/college-admin/faculty/faculty-subject-allocation"),
        (
            "department_assignment",
            "Department assignment",
            4,
            "/college-admin/faculty/department-designation-assignment",
        ),
        ("workload_review", "Workload review", 5, "/college-admin/faculty/faculty-workload-management"),
        ("confirmation", "Confirmation", 6, "/college-admin/faculty/faculty-subject-allocation"),
    ]
    active_index = next((i for i, (k, *_) in enumerate(steps_def) if k == active_key), 2)
    steps: list[FacultyAssignmentWorkflowStep] = []
    for index, (key, label, number, href) in enumerate(steps_def):
        if index < active_index:
            status = "done"
        elif index == active_index:
            status = "active"
        else:
            status = "pending"
        steps.append(
            FacultyAssignmentWorkflowStep(key=key, label=label, step_number=number, status=status, href=href)
        )
    return steps


async def _faculty_in_department(
    tenant_id: PydanticObjectId,
    dept_oid: PydanticObjectId | None,
) -> list[FacultyRecord]:
    records = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    if dept_oid is None:
        return records
    return [r for r in records if r.department_id == dept_oid]


async def _assigned_map(
    tenant_id: PydanticObjectId,
    *,
    year_label: str,
    semester_label: str,
) -> dict[str, tuple[str, str]]:
    assignments = await FacultyAssignment.find(
        Eq(FacultyAssignment.tenant_id, tenant_id),
        Eq(FacultyAssignment.academic_year_label, year_label),
        Eq(FacultyAssignment.status, AssignmentStatus.ACTIVE),
    ).to_list()
    if semester_label:
        assignments = [a for a in assignments if a.semester_label == semester_label]
    course_to_faculty: dict[str, tuple[str, str]] = {}
    faculty_by_user: dict[PydanticObjectId, FacultyRecord] = {}
    for assignment in assignments:
        faculty = faculty_by_user.get(assignment.user_id)
        if faculty is None:
            faculty = await FacultyRecord.find_one(
                Eq(FacultyRecord.tenant_id, tenant_id),
                Eq(FacultyRecord.user_id, assignment.user_id),
            )
            if faculty:
                faculty_by_user[assignment.user_id] = faculty
        if faculty is None:
            continue
        user = await User.get(faculty.user_id)
        name = user.full_name if user else "—"
        key = assignment.course_id or assignment.course_code
        course_to_faculty[key] = (name, str(faculty.id))
    return course_to_faculty


async def _hours_by_faculty(
    tenant_id: PydanticObjectId,
    faculty_rows: list[FacultyRecord],
    *,
    year_label: str,
    semester_label: str,
) -> dict[PydanticObjectId, float]:
    hours: dict[PydanticObjectId, float] = defaultdict(float)
    for record in faculty_rows:
        workload = await FacultyWorkload.find_one(
            Eq(FacultyWorkload.tenant_id, tenant_id),
            Eq(FacultyWorkload.user_id, record.user_id),
            Eq(FacultyWorkload.academic_year_label, year_label),
            Eq(FacultyWorkload.semester_label, semester_label),
        )
        if workload and workload.total_hours > 0:
            hours[record.user_id] = workload.total_hours
            continue
        assignments = await FacultyAssignment.find(
            Eq(FacultyAssignment.tenant_id, tenant_id),
            Eq(FacultyAssignment.user_id, record.user_id),
            Eq(FacultyAssignment.academic_year_label, year_label),
            Eq(FacultyAssignment.semester_label, semester_label),
            Eq(FacultyAssignment.status, AssignmentStatus.ACTIVE),
        ).to_list()
        for item in assignments:
            hours[record.user_id] += 3.0
    return hours


async def _build_page(
    scope: AccessScope,
    *,
    year_label: str,
    semester_label: str,
    department_id: str | None,
    suggestions: dict[str, str] | None = None,
) -> FacultySubjectAllocationPageRead:
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    dept_oid = to_object_id(department_id, "department_id") if department_id else None

    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-year_code").to_list()
    current_year, current_sem = await _reader.current_academic_term(tenant_id)
    selected_year = year_label or current_year or (years[0].label if years else "")
    selected_semester = semester_label or current_sem or _SEMESTER_OPTIONS[0]

    year_options = [
        StudentAdminDashboardFilterOption(value=y.label or y.year_code, label=y.label or y.year_code) for y in years
    ]
    if not year_options and selected_year:
        year_options = [StudentAdminDashboardFilterOption(value=selected_year, label=selected_year)]

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
        Eq(InstitutionDepartment.department_kind, DepartmentKind.ACADEMIC),
    ).to_list()
    if not dept_oid and departments:
        dept_oid = departments[0].id

    dept_options = [StudentAdminDashboardFilterOption(value="", label="All departments")]
    for dept in sorted(departments, key=lambda d: d.name or ""):
        dept_options.append(
            StudentAdminDashboardFilterOption(value=str(dept.id), label=dept.name or dept.department_code or "—"),
        )

    semester_options = [StudentAdminDashboardFilterOption(value=s, label=s) for s in _SEMESTER_OPTIONS]

    courses = await CourseRecord.find(Eq(CourseRecord.tenant_id, tenant_id), Eq(CourseRecord.is_active, True)).to_list()
    if dept_oid:
        courses = [c for c in courses if c.department_id == dept_oid]

    course_map = {c.course_id: c for c in courses}
    assigned = await _assigned_map(tenant_id, year_label=selected_year, semester_label=selected_semester)
    faculty_rows = await _faculty_in_department(tenant_id, dept_oid)
    hours_map = await _hours_by_faculty(
        tenant_id,
        faculty_rows,
        year_label=selected_year,
        semester_label=selected_semester,
    )

    subject_rows: list[FacultySubjectAllocationTableRow] = []
    unassigned_count = 0
    for course in courses[:_SUBJECT_PREVIEW]:
        key = course.course_id
        faculty_label = "—"
        faculty_record_id: str | None = None
        status_label: str | None = None
        status_tone: str | None = None
        if key in assigned:
            faculty_label, faculty_record_id = assigned[key]
        elif suggestions and key in suggestions:
            faculty_record_id = suggestions[key]
            fac = await FacultyRecord.get(to_object_id(faculty_record_id, "faculty_record_id"))
            if fac:
                user = await User.get(fac.user_id)
                faculty_label = user.full_name if user else "—"
        else:
            unassigned_count += 1
            status_label = "Unassigned"
            status_tone = "warning"

        subject_rows.append(
            FacultySubjectAllocationTableRow(
                course_id=course.course_id,
                subject_name=course.name,
                subject_code=course.course_code,
                semester_label=str(course.semester_number or "—"),
                hours_label=str(int(_course_hours(course))),
                faculty_label=faculty_label,
                faculty_record_id=faculty_record_id,
                status_label=status_label,
                status_tone=status_tone,
            )
        )

    assigned_count = len(subject_rows) - unassigned_count
    subjects_footer = f"{assigned_count} of {len(courses) or len(subject_rows)} subject{'s' if len(courses) != 1 else ''}"

    capacity_rows: list[FacultySubjectCapacityRow] = []
    for record in faculty_rows[:8]:
        user = await User.get(record.user_id)
        if user is None:
            continue
        assigned_hours = hours_map.get(record.user_id, 0.0)
        cap = _OVERLOAD_HOURS
        tone = _load_tone(assigned_hours, cap)
        capacity_rows.append(
            FacultySubjectCapacityRow(
                faculty_record_id=str(record.id),
                faculty_name=user.full_name,
                hours_assigned_label=f"{int(round(assigned_hours))} of {int(cap)} h",
                hours_capacity_label=f"{int(round(assigned_hours))} of {int(cap)} h",
                assigned_hours=assigned_hours,
                capacity_hours=cap,
                load_tone=tone,
            )
        )

    subtitle = f"Allocate subjects for {selected_semester} semester {selected_year}"

    return FacultySubjectAllocationPageRead(
        page_title="Faculty Subject Allocation",
        page_subtitle=subtitle,
        auto_suggest_label="Auto-suggest",
        confirm_label="Confirm allocation",
        semester_filter_label="Semester",
        department_filter_label="Department",
        scope_indicator_label="College scope",
        updated_at_label=_fmt_time_label(now),
        academic_year_options=year_options,
        department_options=dept_options,
        semester_options=semester_options,
        selected_academic_year=selected_year,
        selected_department_id=str(dept_oid) if dept_oid else "",
        selected_semester_label=selected_semester,
        workflow_steps=_workflow_steps(),
        subjects_section_title="Subjects to allocate",
        table_headers=["Subject", "Code", "Sem", "Hours", "Faculty"],
        subject_rows=subject_rows,
        subjects_footer_label=subjects_footer,
        capacity_section_title="Faculty capacity",
        capacity_rows=capacity_rows,
        has_pending_suggestions=bool(suggestions),
        footer_disclaimer="Live institutional data · Faculty and employee records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def get_faculty_subject_allocation_page(
    scope: AccessScope,
    *,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    department_id: str | None = None,
) -> FacultySubjectAllocationPageRead:
    authorize(scope, Permission.FACULTY_ADMIN_READ)
    return await _build_page(
        scope,
        year_label=academic_year_label or "",
        semester_label=semester_label or "",
        department_id=department_id,
    )


async def auto_suggest_faculty_subject_allocation(
    scope: AccessScope,
    filters: FacultySubjectAllocationFilterPayload,
) -> FacultySubjectAllocationPageRead:
    authorize(scope, Permission.FACULTY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    year_label = filters.academic_year_label or ""
    semester_label = filters.semester_label or ""
    dept_oid = to_object_id(filters.department_id, "department_id") if filters.department_id else None

    page = await _build_page(scope, year_label=year_label, semester_label=semester_label, department_id=filters.department_id)
    faculty_rows = await _faculty_in_department(tenant_id, dept_oid)
    if not faculty_rows:
        return page

    hours_map = await _hours_by_faculty(
        tenant_id,
        faculty_rows,
        year_label=page.selected_academic_year,
        semester_label=page.selected_semester_label,
    )
    assigned = await _assigned_map(
        tenant_id,
        year_label=page.selected_academic_year,
        semester_label=page.selected_semester_label,
    )

    courses = await CourseRecord.find(Eq(CourseRecord.tenant_id, tenant_id), Eq(CourseRecord.is_active, True)).to_list()
    if dept_oid:
        courses = [c for c in courses if c.department_id == dept_oid]

    suggestions: dict[str, str] = {}
    load: dict[PydanticObjectId, float] = {r.user_id: hours_map.get(r.user_id, 0.0) for r in faculty_rows}
    faculty_by_user = {r.user_id: r for r in faculty_rows}

    for course in courses[:_SUBJECT_PREVIEW]:
        if course.course_id in assigned:
            continue
        need = _course_hours(course)
        pick_user = min(load.keys(), key=lambda uid: load[uid])
        if load[pick_user] + need > _OVERLOAD_HOURS:
            continue
        record = faculty_by_user[pick_user]
        suggestions[course.course_id] = str(record.id)
        load[pick_user] += need

    return await _build_page(
        scope,
        year_label=page.selected_academic_year,
        semester_label=page.selected_semester_label,
        department_id=page.selected_department_id,
        suggestions=suggestions,
    )


async def confirm_faculty_subject_allocation(
    scope: AccessScope,
    payload: FacultySubjectAllocationConfirmPayload,
) -> FacultySubjectAllocationPageRead:
    authorize(scope, Permission.FACULTY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)

    if not payload.allocations:
        raise AppError(code="VALIDATION_ERROR", message="No allocations to confirm", status_code=422)

    courses = await CourseRecord.find(Eq(CourseRecord.tenant_id, tenant_id)).to_list()
    course_by_id = {c.course_id: c for c in courses}

    for row in payload.allocations:
        course = course_by_id.get(row.course_id)
        if course is None:
            continue
        record_id = to_object_id(row.faculty_record_id, "faculty_record_id")
        create_payload = TeachingAssignmentCreate(
            academic_year_label=payload.academic_year_label,
            semester_label=payload.semester_label,
            course_id=course.course_id,
            course_code=course.course_code,
            course_name=course.name,
            subject_code=course.course_code,
            subject_name=course.name,
            section="A",
        )
        existing = await FacultyAssignment.find_one(
            Eq(FacultyAssignment.tenant_id, tenant_id),
            Eq(FacultyAssignment.course_code, course.course_code),
            Eq(FacultyAssignment.academic_year_label, payload.academic_year_label),
            Eq(FacultyAssignment.semester_label, payload.semester_label),
            Eq(FacultyAssignment.status, AssignmentStatus.ACTIVE),
        )
        if existing is not None:
            continue
        await assign_teaching(scope, record_id, create_payload)

    return await get_faculty_subject_allocation_page(
        scope,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        department_id=payload.department_id,
    )