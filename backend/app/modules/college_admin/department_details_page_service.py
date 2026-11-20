"""Department details page (CA 04 — organization)."""

from __future__ import annotations

from collections import defaultdict
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.department_performance_overview_service import _programme_level
from app.modules.college_admin.department_management_dashboard_page_service import _ACTIVE_EMPLOYMENT
from app.modules.college_admin.faculty_admin_models import (
    FacultyEmploymentStatus,
    FacultyRecord,
    FacultyWorkloadRecord,
)
from app.modules.college_admin.finance_ext_models import DepartmentBudgetAllocation
from app.modules.college_admin.identity_models import (
    DepartmentHistory,
    DepartmentStaffAssociation,
    DepartmentStatus,
    InstitutionDepartment,
    InstitutionOrganizationUnit,
)
from app.modules.college_admin.institution_service import list_campuses
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.models import InstitutionCampus
from app.modules.college_admin.operations_ext_models import InstitutionFacility
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    DepartmentDetailsActivityItem,
    DepartmentDetailsFacultyRow,
    DepartmentDetailsPageRead,
    DepartmentDetailsProgrammeRow,
    DepartmentDetailsProfileBadge,
    DepartmentDetailsResourceItem,
    UserDashboardKpi,
)
from app.modules.examinations.exam_cell_grading_enums import ExamSubjectResultOutcome
from app.modules.examinations.exam_cell_grading_models import ExamStudentSubjectResult
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.faculty.models import FacultyProfile
from app.modules.students.models import StudentProfile

_IST = ZoneInfo("Asia/Kolkata")
_reader = OperationalDataReader()
_FACULTY_PREVIEW = 6
_PROGRAMME_PREVIEW = 8
_WORKLOAD_WARN_HOURS = 18.0
_ATTENDANCE_THRESHOLD = 75.0

_LEVEL_LABEL = {
    "undergraduate": "UG",
    "postgraduate": "PG",
    "doctoral": "Doctoral",
}


def _format_ist(when, *, time_only: bool = False) -> str:
    local = as_utc_aware(when).astimezone(_IST)
    if time_only:
        today = utcnow().astimezone(_IST).date()
        if local.date() == today:
            return f"Today {local.strftime('%H:%M')}"
        return local.strftime("%d %b")
    return local.strftime("%d %b %Y, %H:%M")


def _format_budget(amount: float, currency: str = "INR") -> str:
    if currency == "INR":
        if amount >= 10_000_000:
            return f"₹{amount / 10_000_000:.1f} Cr"
        if amount >= 100_000:
            return f"₹{amount / 100_000:.1f} lakh"
        return f"₹{amount:,.0f}"
    return f"{currency} {amount:,.0f}"


def _designation_bucket(designation: str | None) -> str | None:
    if not designation:
        return None
    lower = designation.lower()
    if "professor" in lower and "assistant" not in lower and "associate" not in lower:
        return "professor"
    if "associate" in lower:
        return "associate"
    if "assistant" in lower:
        return "assistant"
    return None


def _faculty_status(employment_status: FacultyEmploymentStatus, total_hours: float | None) -> tuple[str, str, str]:
    if employment_status == FacultyEmploymentStatus.ON_LEAVE:
        return "on_leave", "On leave", "info"
    if total_hours is not None and total_hours >= _WORKLOAD_WARN_HOURS:
        return "overloaded", "Overloaded", "warning"
    if employment_status in _ACTIVE_EMPLOYMENT:
        return "active", "Active", "success"
    return "inactive", "Inactive", "muted"


def _status_badge(status: DepartmentStatus) -> DepartmentDetailsProfileBadge:
    if status == DepartmentStatus.ACTIVE:
        return DepartmentDetailsProfileBadge(key="status", label="Active", tone="success")
    if status == DepartmentStatus.DRAFT:
        return DepartmentDetailsProfileBadge(key="status", label="Draft", tone="warning")
    if status == DepartmentStatus.ARCHIVED:
        return DepartmentDetailsProfileBadge(key="status", label="Archived", tone="muted")
    return DepartmentDetailsProfileBadge(key="status", label="Inactive", tone="muted")


async def get_department_details_page(
    scope: AccessScope,
    department_id: PydanticObjectId,
) -> DepartmentDetailsPageRead:
    authorize(scope, Permission.INSTITUTION_ORG_READ)
    tenant_id = require_college_tenant_scope(scope)

    dept = await InstitutionDepartment.get(department_id)
    if dept is None or dept.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Department not found", status_code=404)

    school_label = ""
    if dept.organization_unit_id:
        unit = await InstitutionOrganizationUnit.get(dept.organization_unit_id)
        if unit:
            school_label = unit.name

    campus_label = ""
    if dept.campus_ids:
        campus_doc = await InstitutionCampus.get(dept.campus_ids[0])
        if campus_doc:
            campus_label = campus_doc.name
    else:
        campuses = await list_campuses(scope, active_only=True)
        if campuses:
            campus_label = campuses[0].name

    location_parts = [dept.department_code]
    if school_label:
        location_parts.append(school_label)
    loc_suffix = dept.building_floor_label or ""
    if loc_suffix and campus_label:
        loc_suffix = f"{loc_suffix}, {campus_label}"
    elif campus_label:
        loc_suffix = campus_label
    if loc_suffix:
        location_parts.append(loc_suffix)
    if dept.establishment_year:
        location_parts.append(f"Est. {dept.establishment_year}")
    metadata_line = " · ".join(location_parts)

    head_label = "—"
    phone_label = "—"
    if dept.head_user_id:
        head_user = await User.get(dept.head_user_id)
        if head_user:
            head_label = head_user.full_name
            profile = await FacultyProfile.find_one(
                Eq(FacultyProfile.tenant_id, tenant_id),
                Eq(FacultyProfile.user_id, head_user.id),
            )
            if profile and profile.contact_phone:
                phone_label = profile.contact_phone

    badges = [_status_badge(dept.status)]
    prog_codes_upper = {c.upper() for c in dept.programme_codes}
    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    dept_programmes = [
        p
        for p in programmes
        if p.is_active and (p.department_id == dept.id or p.programme_code.upper() in prog_codes_upper)
    ]

    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    students_in_dept = [p for p in profiles if p.department_id == dept.id]
    students_by_prog: dict[str, int] = defaultdict(int)
    for profile in students_in_dept:
        code = (profile.programme_code or "").upper()
        if code:
            students_by_prog[code] += 1

    faculty_records = await FacultyRecord.find(
        Eq(FacultyRecord.tenant_id, tenant_id),
        Eq(FacultyRecord.department_id, dept.id),
    ).to_list()
    faculty_user_ids = {r.user_id for r in faculty_records if r.employment_status in _ACTIVE_EMPLOYMENT}
    faculty_profiles = await FacultyProfile.find(
        Eq(FacultyProfile.tenant_id, tenant_id),
        Eq(FacultyProfile.department_id, dept.id),
    ).to_list()
    for fp in faculty_profiles:
        if fp.user_id not in {r.user_id for r in faculty_records}:
            faculty_user_ids.add(fp.user_id)

    faculty_users = (
        await User.find(In(User.id, list(faculty_user_ids))).to_list() if faculty_user_ids else []
    )
    user_by_id = {u.id: u for u in faculty_users}

    year_label, _sem = await _reader.current_academic_term(tenant_id)
    workloads = await FacultyWorkloadRecord.find(Eq(FacultyWorkloadRecord.tenant_id, tenant_id)).to_list()
    wl_by_user = {
        w.user_id: w.total_hours
        for w in workloads
        if w.academic_year_label == year_label or not year_label
    }

    buckets = {"professor": 0, "associate": 0, "assistant": 0}
    for rec in faculty_records:
        if rec.employment_status not in _ACTIVE_EMPLOYMENT:
            continue
        bucket = _designation_bucket(rec.designation)
        if bucket in buckets:
            buckets[bucket] += 1
    faculty_hint_parts = [
        f"{buckets['professor']} Prof" if buckets["professor"] else None,
        f"{buckets['associate']} Assoc" if buckets["associate"] else None,
        f"{buckets['assistant']} Asst" if buckets["assistant"] else None,
    ]
    faculty_hint = " · ".join(p for p in faculty_hint_parts if p) or "Faculty records"

    exam_sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).to_list()
    if year_label:
        exam_sessions = [s for s in exam_sessions if s.academic_year_label == year_label]
    session_ids = [s.id for s in exam_sessions]
    user_dept = {p.user_id: p.department_id for p in students_in_dept}
    passed, failed = 0, 0
    results: list[ExamStudentSubjectResult] = []
    if session_ids:
        results = await ExamStudentSubjectResult.find(
            Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
            In(ExamStudentSubjectResult.exam_session_id, session_ids),
        ).to_list()
        for row in results:
            if user_dept.get(row.student_user_id) != dept.id:
                continue
            if row.outcome == ExamSubjectResultOutcome.PASS:
                passed += 1
            elif row.outcome == ExamSubjectResultOutcome.FAIL:
                failed += 1
    total_results = passed + failed
    pass_rate = round((passed / total_results) * 100, 1) if total_results else None

    all_student_dept = {p.user_id: p.department_id for p in profiles if p.department_id}
    all_pass_rates: list[float] = []
    if session_ids and results:
        all_dept_ids = {
            d.id for d in await InstitutionDepartment.find(Eq(InstitutionDepartment.tenant_id, tenant_id)).to_list()
        }
        for other_id in all_dept_ids:
            op, of = 0, 0
            for row in results:
                if all_student_dept.get(row.student_user_id) != other_id:
                    continue
                if row.outcome == ExamSubjectResultOutcome.PASS:
                    op += 1
                elif row.outcome == ExamSubjectResultOutcome.FAIL:
                    of += 1
            ot = op + of
            if ot:
                all_pass_rates.append((op / ot) * 100)
    college_avg = round(sum(all_pass_rates) / len(all_pass_rates), 1) if all_pass_rates else None
    pass_hint = (
        "Best in college"
        if pass_rate is not None and college_avg is not None and pass_rate >= college_avg
        else ("Below college average" if pass_rate is not None and college_avg is not None and pass_rate < college_avg else "No exam data yet")
    )
    pass_tone = "success" if pass_hint == "Best in college" else "muted"

    attendance_present = 0
    attendance_total = 0
    below_threshold = 0
    from app.modules.attendance.enums import AttendanceMarkStatus, AttendanceSessionStatus
    from app.modules.attendance.models import AttendanceRecord, AttendanceSession

    att_sessions = await AttendanceSession.find(
        Eq(AttendanceSession.tenant_id, tenant_id),
        Eq(AttendanceSession.status, AttendanceSessionStatus.SUBMITTED),
    ).to_list()
    if year_label:
        att_sessions = [s for s in att_sessions if s.academic_year_label == year_label]
    att_session_ids = {s.id for s in att_sessions}
    present_marks = {
        AttendanceMarkStatus.PRESENT,
        AttendanceMarkStatus.LATE,
        AttendanceMarkStatus.EXCUSED,
    }
    student_att: dict[PydanticObjectId, list[int]] = defaultdict(lambda: [0, 0])
    if att_session_ids:
        records = await AttendanceRecord.find(
            Eq(AttendanceRecord.tenant_id, tenant_id),
            In(AttendanceRecord.session_id, list(att_session_ids)),
        ).to_list()
        for rec in records:
            if user_dept.get(rec.student_user_id) != dept.id:
                continue
            if rec.status in present_marks:
                student_att[rec.student_user_id][0] += 1
                attendance_present += 1
            else:
                student_att[rec.student_user_id][1] += 1
            attendance_total += 1
        for counts in student_att.values():
            total = counts[0] + counts[1]
            if total and (counts[0] / total) * 100 < _ATTENDANCE_THRESHOLD:
                below_threshold += 1
    attendance_pct = round((attendance_present / attendance_total) * 100, 1) if attendance_total else None
    att_hint = (
        f"{below_threshold} student{'s' if below_threshold != 1 else ''} below {_ATTENDANCE_THRESHOLD:.0f}%"
        if below_threshold
        else ("Strong attendance" if attendance_pct and attendance_pct >= 85 else "No attendance data yet")
    )

    kpis = [
        UserDashboardKpi(
            key="students",
            label="Students",
            value=f"{len(students_in_dept):,}",
            hint_line=f"{len(dept_programmes)} programme{'s' if len(dept_programmes) != 1 else ''}",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="faculty",
            label="Faculty",
            value=str(len(faculty_user_ids)),
            hint_line=faculty_hint,
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="pass_rate",
            label="Pass rate",
            value=f"{pass_rate}%" if pass_rate is not None else "—",
            hint_line=pass_hint,
            hint_tone=pass_tone,
        ),
        UserDashboardKpi(
            key="attendance",
            label="Attendance",
            value=f"{attendance_pct}%" if attendance_pct is not None else "—",
            hint_line=att_hint,
            hint_tone="warning" if below_threshold else "muted",
        ),
    ]

    programme_rows: list[DepartmentDetailsProgrammeRow] = []
    for prog in sorted(dept_programmes, key=lambda p: p.name):
        code = prog.programme_code.upper()
        student_count = students_by_prog.get(code, 0)
        status_label = "Running" if dept.status == DepartmentStatus.ACTIVE and prog.is_active else "Draft"
        status_tone = "success" if status_label == "Running" else "muted"
        programme_rows.append(
            DepartmentDetailsProgrammeRow(
                programme_id=str(prog.id),
                programme_name=prog.name,
                level_label=_LEVEL_LABEL.get(_programme_level(prog), "UG"),
                intake=dept.approved_intake_ug if _programme_level(prog) == "undergraduate" else None,
                student_count=student_count,
                status_code=status_label.lower(),
                status_label=status_label,
                status_tone=status_tone,
            )
        )

    faculty_rows: list[DepartmentDetailsFacultyRow] = []
    rec_by_user = {r.user_id: r for r in faculty_records}
    def _faculty_sort_key(uid: PydanticObjectId) -> str:
        user = user_by_id.get(uid)
        return user.full_name.lower() if user else ""

    for uid in sorted(faculty_user_ids, key=_faculty_sort_key):
        user = user_by_id.get(uid)
        if not user:
            continue
        rec = rec_by_user.get(uid)
        designation = (rec.designation if rec and rec.designation else None) or "Faculty"
        if dept.head_user_id == uid and "head" not in designation.lower():
            designation = f"{designation} & Head"
        hours = wl_by_user.get(uid)
        workload_label = f"{int(hours)} hrs/wk" if hours is not None else "—"
        emp_status = rec.employment_status if rec else FacultyEmploymentStatus.ACTIVE
        status_code, status_label, status_tone = _faculty_status(emp_status, hours)
        faculty_rows.append(
            DepartmentDetailsFacultyRow(
                user_id=str(uid),
                name=user.full_name,
                designation=designation,
                workload_label=workload_label,
                status_code=status_code,
                status_label=status_label,
                status_tone=status_tone,
            )
        )

    campus_oid = dept.campus_ids[0] if dept.campus_ids else None
    facilities = await InstitutionFacility.find(Eq(InstitutionFacility.tenant_id, tenant_id), Eq(InstitutionFacility.active, True)).to_list()
    if campus_oid:
        facilities = [f for f in facilities if f.campus_id == campus_oid or f.campus_id is None]
    classrooms = sum(1 for f in facilities if f.facility_type == "classroom")
    laboratories = sum(1 for f in facilities if f.facility_type == "laboratory")

    allocations = await DepartmentBudgetAllocation.find(
        Eq(DepartmentBudgetAllocation.tenant_id, tenant_id),
        Eq(DepartmentBudgetAllocation.department_id, dept.id),
    ).to_list()
    budget_total = sum(a.allocated_amount for a in allocations)
    budget_label = _format_budget(budget_total) if budget_total else "Not allocated"

    resources = [
        DepartmentDetailsResourceItem(key="classrooms", title="Classrooms", value=str(classrooms)),
        DepartmentDetailsResourceItem(key="laboratories", title="Laboratories", value=str(laboratories)),
        DepartmentDetailsResourceItem(
            key="library",
            title="Department library",
            value="See central library" if classrooms else "—",
        ),
        DepartmentDetailsResourceItem(key="budget", title="Annual budget", value=budget_label),
    ]

    history = await DepartmentHistory.find(
        Eq(DepartmentHistory.tenant_id, tenant_id),
        Eq(DepartmentHistory.department_id, dept.id),
    ).sort("-created_at").limit(8).to_list()
    activities: list[DepartmentDetailsActivityItem] = []
    for item in history:
        tone = "success" if item.change_type == "created" else "info"
        title = {
            "created": "Department record created",
            "updated": "Department profile updated",
            "head_assigned": "Head of department assigned",
        }.get(item.change_type, item.change_type.replace("_", " ").title())
        activities.append(
            DepartmentDetailsActivityItem(
                activity_id=str(item.id),
                title=title,
                occurred_label=_format_ist(item.created_at, time_only=True),
                tone=tone,
            )
        )
    if not activities:
        activities.append(
            DepartmentDetailsActivityItem(
                activity_id="snapshot",
                title="Department profile loaded",
                occurred_label=_format_ist(utcnow(), time_only=True),
                tone="muted",
            )
        )

    acting = False
    associations = await DepartmentStaffAssociation.find(Eq(DepartmentStaffAssociation.tenant_id, tenant_id)).to_list()
    for assoc in associations:
        if str(assoc.department_id) == str(dept.id) and "acting" in (assoc.association_role or "").lower():
            acting = True
            break
    if acting and head_label != "—":
        head_label = f"{head_label} (acting)"

    return DepartmentDetailsPageRead(
        page_title="Department Details",
        page_subtitle=f"Overview of the {dept.name} department",
        back_href="/college-admin/organization/all-departments",
        back_label="All departments",
        view_report_label="View report",
        view_report_href=f"/college-admin/dashboard/department-performance",
        edit_department_label="Edit department",
        edit_department_href=f"/college-admin/organization/department-edit?departmentId={dept.id}",
        department_id=str(dept.id),
        department_name=dept.name,
        department_code=dept.department_code,
        metadata_line=metadata_line,
        head_label=head_label,
        email_label=dept.contact_email or "—",
        phone_label=phone_label,
        profile_badges=badges,
        kpis=kpis,
        programmes_section_title="Programmes",
        programme_mapping_href="/college-admin/organization/programme-course-mapping",
        programme_mapping_label="Programme mapping",
        programmes=programme_rows[:_PROGRAMME_PREVIEW],
        programmes_total=len(programme_rows),
        programmes_footer_label=f"{len(programme_rows)} programme{'s' if len(programme_rows) != 1 else ''}",
        programmes_view_all_href="/college-admin/organization/programme-course-mapping",
        faculty_section_title="Faculty",
        faculty_allocation_href="/college-admin/organization/department-faculty-allocation",
        faculty_allocation_label="Faculty allocation",
        faculty=faculty_rows[:_FACULTY_PREVIEW],
        faculty_total=len(faculty_rows),
        faculty_footer_label=f"{len(faculty_rows)} faculty",
        faculty_view_all_href="/college-admin/organization/department-faculty-allocation",
        resources_section_title="Resources",
        resources=resources,
        activity_section_title="Recent activity",
        activities=activities,
        table_programme_headers=["Programme", "Level", "Intake", "Students", "Status"],
        table_faculty_headers=["Name", "Designation", "Workload", "Status"],
        footer_disclaimer="Live institutional data · Department, academic and staffing records · All times IST",
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )


async def get_department_details_page_by_id(scope: AccessScope, department_id_raw: str) -> DepartmentDetailsPageRead:
    department_oid = to_object_id(department_id_raw, "department_id")
    return await get_department_details_page(scope, department_oid)