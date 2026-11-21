"""Faculty profile page (CA 07.03)."""

from __future__ import annotations

from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import (
    EmployeeRecord,
    FacultyEmploymentStatus,
    FacultyRecord,
    FacultyWorkloadRecord,
)
from app.modules.college_admin.faculty_employee_dashboard_page_service import _status_for_row
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    FacultyProfilePageRead,
    FacultyProfileQualificationRow,
    FacultyProfileSubjectRow,
    StudentDetailsBadge,
    StudentDetailsKeyValueRow,
)
from app.modules.faculty.enums import AssignmentStatus
from app.modules.faculty.models import FacultyAssignment, FacultyProfile, FacultyWorkload, QualificationRecord

_IST = ZoneInfo("Asia/Kolkata")
_reader = OperationalDataReader()


def _initials(full_name: str) -> str:
    parts = [p for p in full_name.strip().split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return f"{parts[0][0]}{parts[-1][0]}".upper()


def _joined_label(joining_date) -> str:
    if joining_date is None:
        return "Joined —"
    return f"Joined {joining_date.strftime('%d %b %Y')}"


def _employment_type_label(employment_type: str | None) -> str:
    if not employment_type:
        return "—"
    return employment_type.replace("_", " ").strip().title()


def _is_lab_course(name: str | None, code: str | None) -> bool:
    blob = f"{name or ''} {code or ''}".lower()
    return any(k in blob for k in ("lab", "laboratory", "practical", "workshop"))


def _qualification_rows(quals: list[QualificationRecord]) -> list[FacultyProfileQualificationRow]:
    rows: list[FacultyProfileQualificationRow] = []
    for q in quals:
        year_label = str(q.year) if q.year else "—"
        rows.append(
            FacultyProfileQualificationRow(
                degree=q.degree,
                institution=q.institution or "—",
                year_label=year_label,
            )
        )
    return rows


def _hours_label(value: float | None) -> str:
    if value is None:
        return "—"
    if abs(value - round(value)) < 0.05:
        return str(int(round(value)))
    return f"{value:.1f}"


def _subject_rows(
    assignments: list[FacultyAssignment],
    *,
    lecture_hours: float,
    lab_hours: float,
) -> list[FacultyProfileSubjectRow]:
    if not assignments:
        return []
    theory = [a for a in assignments if not _is_lab_course(a.course_name or a.subject_name, a.course_code)]
    labs = [a for a in assignments if _is_lab_course(a.course_name or a.subject_name, a.course_code)]
    per_theory = round(lecture_hours / len(theory), 1) if theory and lecture_hours > 0 else None
    per_lab = round(lab_hours / len(labs), 1) if labs and lab_hours > 0 else None

    rows: list[FacultyProfileSubjectRow] = []
    for item in assignments:
        is_lab = item in labs
        hours = per_lab if is_lab else per_theory
        subject_name = item.subject_name or item.course_name or "—"
        programme_sem = item.semester_label or "—"
        if item.section and item.section != "—":
            programme_sem = f"{programme_sem} · Sec {item.section}" if programme_sem != "—" else f"Sec {item.section}"
        rows.append(
            FacultyProfileSubjectRow(
                subject_name=subject_name,
                subject_code=item.subject_code or item.course_code or "—",
                programme_sem_label=programme_sem,
                hours_label=_hours_label(hours),
                type_label="Lab" if is_lab else "Theory",
            )
        )
    return rows


async def get_faculty_profile_page(scope: AccessScope, record_id_raw: str) -> FacultyProfilePageRead:
    authorize(scope, Permission.FACULTY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    record_id = to_object_id(record_id_raw, "record_id")
    now = utcnow()
    year_label, semester_label = await _reader.current_academic_term(tenant_id)

    record = await FacultyRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Faculty record not found", status_code=404)

    user = await User.find_one(Eq(User.id, record.user_id), Eq(User.tenant_id, tenant_id))
    if user is None:
        raise AppError(code="NOT_FOUND", message="Faculty user not found", status_code=404)

    employee = await EmployeeRecord.find_one(
        Eq(EmployeeRecord.tenant_id, tenant_id),
        Eq(EmployeeRecord.user_id, record.user_id),
    )
    profile = await FacultyProfile.find_one(
        Eq(FacultyProfile.tenant_id, tenant_id),
        Eq(FacultyProfile.user_id, record.user_id),
    )

    dept_name = "—"
    dept_code = ""
    reporting_label = "—"
    if record.department_id:
        dept = await InstitutionDepartment.get(record.department_id)
        if dept:
            dept_name = dept.name or dept.department_code
            dept_code = dept.department_code or ""
            if dept.head_user_id:
                head = await User.get(dept.head_user_id)
                if head:
                    short = dept_code or (dept.name[:12] if dept.name else "Dept")
                    reporting_label = f"HOD, {short}"

    employee_id = (employee.employee_id if employee and employee.employee_id else None) or record.faculty_code or "—"
    designation = record.designation or (profile.designation if profile else None) or "—"
    profile_summary = f"{designation} · {dept_name} · {employee_id}"

    workload_record = await FacultyWorkloadRecord.find(
        Eq(FacultyWorkloadRecord.tenant_id, tenant_id),
        Eq(FacultyWorkloadRecord.user_id, record.user_id),
        Eq(FacultyWorkloadRecord.academic_year_label, year_label),
    ).sort("-created_at").first_or_none()
    faculty_workload = await FacultyWorkload.find_one(
        Eq(FacultyWorkload.tenant_id, tenant_id),
        Eq(FacultyWorkload.user_id, record.user_id),
        Eq(FacultyWorkload.academic_year_label, year_label),
        Eq(FacultyWorkload.semester_label, semester_label),
    )

    lecture_hours = 0.0
    lab_hours = 0.0
    total_weekly = 0.0
    if faculty_workload:
        lecture_hours = faculty_workload.lecture_hours
        lab_hours = faculty_workload.lab_hours
        total_weekly = faculty_workload.total_hours or (lecture_hours + lab_hours + faculty_workload.tutorial_hours)
    elif workload_record:
        lecture_hours = workload_record.lecture_hours
        lab_hours = workload_record.lab_hours
        total_weekly = workload_record.total_hours or (lecture_hours + lab_hours + workload_record.tutorial_hours)

    assignments = await FacultyAssignment.find(
        Eq(FacultyAssignment.tenant_id, tenant_id),
        Eq(FacultyAssignment.user_id, record.user_id),
        Eq(FacultyAssignment.academic_year_label, year_label),
        Eq(FacultyAssignment.status, AssignmentStatus.ACTIVE),
    ).to_list()
    if semester_label:
        assignments = [a for a in assignments if a.semester_label == semester_label]

    qualifications = record.qualifications or (profile.qualifications if profile else [])
    qual_rows = _qualification_rows(qualifications)
    subject_rows = _subject_rows(assignments, lecture_hours=lecture_hours, lab_hours=lab_hours)

    assigned_hours = 0.0
    for row in subject_rows:
        try:
            if row.hours_label != "—":
                assigned_hours += float(row.hours_label)
        except ValueError:
            pass
    workload_cap = total_weekly if total_weekly > 0 else assigned_hours
    subjects_footer = (
        f"{int(round(assigned_hours)) if assigned_hours else 0} of {int(round(workload_cap)) if workload_cap else 0} weekly hours"
        if workload_cap
        else "No weekly workload recorded"
    )

    status_label, status_tone = _status_for_row(
        employment_status=record.employment_status,
        workload_hours=total_weekly if total_weekly > 0 else None,
    )
    status_badge = StudentDetailsBadge(key="employment_status", label=status_label, tone=status_tone)

    employment_type_badge = None
    if employee and employee.employment_type:
        tone = "info" if "permanent" in employee.employment_type.lower() else "muted"
        employment_type_badge = StudentDetailsBadge(
            key="employment_type",
            label=_employment_type_label(employee.employment_type),
            tone=tone,
        )
    elif record.employment_status == FacultyEmploymentStatus.CONFIRMED:
        employment_type_badge = StudentDetailsBadge(key="employment_type", label="Permanent", tone="info")

    phone = "—"
    if profile and profile.contact_phone:
        phone = profile.contact_phone
    elif employee and isinstance(employee.confidential_hr, dict):
        phone = str(employee.confidential_hr.get("phone") or employee.confidential_hr.get("mobile") or "—")

    weekly_label = f"{int(round(total_weekly))} hours" if total_weekly > 0 else "—"

    employment_rows = [
        StudentDetailsKeyValueRow(key="department", label="Department", value=dept_name),
        StudentDetailsKeyValueRow(key="designation", label="Designation", value=designation),
        StudentDetailsKeyValueRow(key="reporting", label="Reporting to", value=reporting_label),
        StudentDetailsKeyValueRow(
            key="employee_type",
            label="Employee type",
            value=_employment_type_label(employee.employment_type if employee else None),
        ),
        StudentDetailsKeyValueRow(key="weekly_workload", label="Weekly workload", value=weekly_label),
    ]

    return FacultyProfilePageRead(
        page_title="Faculty Profile",
        page_subtitle="Professional and academic details",
        edit_label="Edit",
        edit_href=f"/college-admin/faculty/employee-profile-management?id={record_id}",
        timetable_label="Timetable",
        timetable_href=f"/college-admin/faculty/faculty-timetable?id={record_id}",
        back_href="/college-admin/faculty/faculty-directory",
        back_label="Back to faculty directory",
        record_id=str(record.id),
        profile_initials=_initials(user.full_name),
        profile_name=user.full_name,
        status_badge=status_badge,
        employment_type_badge=employment_type_badge,
        profile_summary_line=profile_summary,
        email=user.email,
        phone=phone,
        joined_label=_joined_label(employee.joining_date if employee else None),
        qualifications_section_title="Qualifications",
        qualifications_headers=["Degree", "Institution", "Year"],
        qualification_rows=qual_rows,
        qualifications_footer_label=f"{len(qual_rows)} qualification{'s' if len(qual_rows) != 1 else ''}",
        subjects_section_title="Subject allocation",
        subjects_headers=["Subject", "Code", "Programme / sem", "Hours", "Type"],
        subject_rows=subject_rows,
        subjects_footer_label=subjects_footer,
        employment_section_title="Employment",
        employment_rows=employment_rows,
        footer_disclaimer="Live institutional data · Faculty and employee records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )