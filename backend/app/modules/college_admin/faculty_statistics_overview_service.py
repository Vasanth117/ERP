"""Aggregate faculty & employee statistics for the college admin dashboard."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date, timedelta

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.modules.auth.models import User
from app.modules.college_admin.enums import DashboardDateRange
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus, FacultyRecord
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.models import InstitutionSettings
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AcademicTermSummary,
    AvailabilityOverviewItem,
    DistributionItem,
    FacultyDepartmentCountItem,
    FacultyStatisticsFilters,
    FacultyStatisticsKpiRead,
    FacultyStatisticsOverviewRead,
    RecentJoinerRow,
)
from app.modules.faculty.models import FacultyProfile, QualificationRecord
from app.modules.hr.attendance_schedule_models import HrEmployeeAttendanceRecord
from app.modules.hr.enums import (
    EmployeeAttendanceDayStatus,
    HrJobOpeningStatus,
    HrOnboardingProcessStatus,
    HrOnboardingTaskStatus,
    LeaveRequestStatus,
)
from app.modules.hr.models import LeaveRequest
from app.modules.hr.onboarding_models import HrOnboardingProcess, HrOnboardingTask
from app.modules.hr.recruitment_models import HrJobOpening, HrJobRequisition

_reader = OperationalDataReader()

_ACTIVE_EMPLOYMENT = frozenset(
    {
        FacultyEmploymentStatus.ACTIVE,
        FacultyEmploymentStatus.CONFIRMED,
        FacultyEmploymentStatus.PROBATION,
        FacultyEmploymentStatus.AWAITING_CONFIRMATION,
        FacultyEmploymentStatus.ON_LEAVE,
    }
)

_PRESENT_STATUSES = frozenset(
    {
        EmployeeAttendanceDayStatus.PRESENT,
        EmployeeAttendanceDayStatus.LATE,
        EmployeeAttendanceDayStatus.WORK_FROM_HOME,
        EmployeeAttendanceDayStatus.HALF_DAY,
        EmployeeAttendanceDayStatus.EARLY_DEPARTURE,
    }
)

_DESIGNATION_BUCKETS: tuple[tuple[str, str], ...] = (
    ("professor", "Professors"),
    ("associate_professor", "Associate Professors"),
    ("assistant_professor", "Assistant Professors"),
    ("visiting", "Visiting / adjunct faculty"),
)


def _norm_designation(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _is_visiting(employment_type: str | None, designation: str | None) -> bool:
    blob = f"{employment_type or ''} {designation or ''}".lower()
    return any(k in blob for k in ("visiting", "adjunct", "guest", "contract faculty"))


def _designation_bucket(designation: str | None) -> str | None:
    d = _norm_designation(designation)
    if not d:
        return None
    if _is_visiting(None, d):
        return "visiting"
    if "assistant professor" in d or d.startswith("asst"):
        return "assistant_professor"
    if "associate professor" in d:
        return "associate_professor"
    if re.search(r"\bprofessor\b", d) and "assistant" not in d and "associate" not in d:
        return "professor"
    return None


def _qualification_bucket(quals: list[QualificationRecord]) -> str | None:
    for q in quals:
        deg = (q.degree or "").lower()
        if "pursuing" in deg and ("ph" in deg or "doctor" in deg):
            return "pursuing_phd"
        if re.search(r"ph\.?\s*d|doctor of philosophy|doctorate", deg):
            return "phd"
    for q in quals:
        deg = (q.degree or "").lower()
        if re.search(r"m\.?\s*e|m\.?\s*tech|m\.?\s*sc|master|m\.?\s*ba|pg", deg):
            return "pg"
    return None


def _qualification_label(key: str) -> str:
    return {
        "phd": "Ph.D.",
        "pursuing_phd": "Pursuing Ph.D.",
        "pg": "M.E. / M.Tech / PG",
    }.get(key, key)


def _is_teaching_role(employment_type: str | None, designation: str | None, is_faculty: bool) -> bool:
    if is_faculty:
        return True
    blob = f"{employment_type or ''} {designation or ''}".lower()
    if any(k in blob for k in ("non-teaching", "admin", "accounts", "support staff", "clerical")):
        return False
    return any(k in blob for k in ("faculty", "professor", "lecturer", "teaching", "academic"))


def _is_teaching_opening(requisition: HrJobRequisition | None, job_title: str) -> bool:
    if requisition is None:
        blob = job_title.lower()
    else:
        blob = f"{requisition.employment_type} {requisition.job_title} {job_title}".lower()
    if any(k in blob for k in ("non-teaching", "accounts", "administration", "lab technician", "support")):
        return False
    return any(k in blob for k in ("professor", "faculty", "lecturer", "teaching", "assistant professor"))


def _employee_active(status: FacultyEmploymentStatus) -> bool:
    return status in _ACTIVE_EMPLOYMENT


def _distribution(counts: dict[str, int]) -> list[DistributionItem]:
    total = sum(counts.values())
    items: list[DistributionItem] = []
    for key, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        label = _qualification_label(key) if key in {"phd", "pursuing_phd", "pg"} else key
        if key in dict(_DESIGNATION_BUCKETS):
            label = dict(_DESIGNATION_BUCKETS)[key]
        share = round((count / total) * 100, 1) if total else None
        items.append(DistributionItem(key=key, label=label, count=count, share_pct=share))
    return items


async def _onboarding_status_label(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    employment_status: FacultyEmploymentStatus,
) -> tuple[str, str]:
    proc = await HrOnboardingProcess.find(
        Eq(HrOnboardingProcess.tenant_id, tenant_id),
        Eq(HrOnboardingProcess.employee_user_id, user_id),
    ).sort("-created_at").first_or_none()
    if proc is None:
        if employment_status in (FacultyEmploymentStatus.CONFIRMED, FacultyEmploymentStatus.ACTIVE):
            return "completed", "Completed"
        return "in_progress", "In progress"
    if proc.status == HrOnboardingProcessStatus.COMPLETED:
        return "completed", "Completed"
    pending_docs = await HrOnboardingTask.find(
        Eq(HrOnboardingTask.tenant_id, tenant_id),
        Eq(HrOnboardingTask.process_id, proc.id),
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
    if any("document" in (t.title or "").lower() for t in pending_docs):
        return "documents_due", "Documents due"
    return "in_progress", "In progress"


def _ratio_norm_from_settings(settings: InstitutionSettings | None) -> tuple[float | None, str | None]:
    if settings is None:
        return None, None
    raw = settings.settings or {}
    for key in ("student_faculty_ratio_norm", "aict_student_faculty_ratio_max", "compliance_student_faculty_ratio_max"):
        val = raw.get(key)
        if isinstance(val, (int, float)) and val > 0:
            return float(val), raw.get("student_faculty_ratio_regulator") or "Regulatory norm"
    return None, None


async def get_faculty_statistics_overview(
    scope: AccessScope,
    *,
    anchor_date: date | None = None,
    date_range: DashboardDateRange = DashboardDateRange.TODAY,
    department_id: str | None = None,
    designation: str | None = None,
    campus_id: str | None = None,
) -> FacultyStatisticsOverviewRead:
    authorize(scope, Permission.COLLEGE_DASHBOARD_READ)
    tenant_id = require_college_tenant_scope(scope)

    dept_oid = to_object_id(department_id, "department_id") if department_id else None
    campus_oid = to_object_id(campus_id, "campus_id") if campus_id else None
    anchor = anchor_date or date.today()
    designation_filter = _norm_designation(designation) if designation else None

    year, semester = await _reader.current_academic_term(tenant_id)
    headcount = await _reader.headcount_statistics(tenant_id, department_id=dept_oid)
    inst_settings = await InstitutionSettings.find_one(Eq(InstitutionSettings.tenant_id, tenant_id))
    ratio_max, ratio_label = _ratio_norm_from_settings(inst_settings)

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    dept_by_id = {d.id: d for d in departments}

    campus_dept_ids: set[PydanticObjectId] | None = None
    if campus_oid is not None:
        campus_dept_ids = {d.id for d in departments if campus_oid in d.campus_ids}

    faculty_records = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    employee_records = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    faculty_profiles = await FacultyProfile.find(Eq(FacultyProfile.tenant_id, tenant_id)).to_list()
    profile_by_user = {p.user_id: p for p in faculty_profiles}
    employee_by_user = {e.user_id: e for e in employee_records}

    def faculty_row_matches(rec: FacultyRecord) -> bool:
        if not _employee_active(rec.employment_status):
            return False
        if dept_oid and rec.department_id != dept_oid:
            return False
        if campus_dept_ids is not None and rec.department_id and rec.department_id not in campus_dept_ids:
            return False
        if designation_filter and _norm_designation(rec.designation) != designation_filter:
            return False
        return True

    def employee_row_matches(emp: EmployeeRecord) -> bool:
        if not _employee_active(emp.employment_status):
            return False
        if dept_oid and emp.department_id != dept_oid:
            return False
        if campus_dept_ids is not None and emp.department_id and emp.department_id not in campus_dept_ids:
            return False
        if designation_filter and _norm_designation(emp.designation) != designation_filter:
            return False
        return True

    active_faculty = [r for r in faculty_records if faculty_row_matches(r)]
    seen_faculty_users = {r.user_id for r in active_faculty}
    for profile in faculty_profiles:
        if profile.user_id in seen_faculty_users:
            continue
        if dept_oid and profile.department_id != dept_oid:
            continue
        if campus_dept_ids is not None and profile.department_id and profile.department_id not in campus_dept_ids:
            continue
        if designation_filter and _norm_designation(profile.designation) != designation_filter:
            continue
        active_faculty.append(
            FacultyRecord(
                tenant_id=tenant_id,
                user_id=profile.user_id,
                designation=profile.designation,
                department_id=profile.department_id,
                qualifications=profile.qualifications,
                employment_status=FacultyEmploymentStatus.ACTIVE,
            )
        )
        seen_faculty_users.add(profile.user_id)

    teaching_regular = 0
    teaching_visiting = 0
    for rec in active_faculty:
        emp = employee_by_user.get(rec.user_id)
        employment_type = emp.employment_type if emp else None
        if _is_visiting(employment_type, rec.designation):
            teaching_visiting += 1
        else:
            teaching_regular += 1

    non_teaching = sum(
        1
        for emp in employee_records
        if employee_row_matches(emp) and not emp.is_faculty and not _is_teaching_role(emp.employment_type, emp.designation, emp.is_faculty)
    )
    if non_teaching == 0:
        non_teaching = sum(
            1
            for emp in employee_records
            if employee_row_matches(emp) and not emp.is_faculty
        )

    teaching_total = teaching_regular + teaching_visiting
    ratio_display = None
    ratio_value = None
    meets_norm = None
    if teaching_total > 0 and headcount.total_students > 0:
        ratio_value = round(headcount.total_students / teaching_total, 1)
        ratio_display = f"{int(round(ratio_value))} : 1"
        if ratio_max:
            meets_norm = ratio_value <= ratio_max

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
    open_total = open_teaching = open_non_teaching = 0
    for opening in openings:
        open_slots = max(0, opening.vacancies - opening.filled_count)
        if open_slots == 0:
            continue
        req = req_by_id.get(opening.requisition_id)
        if _is_teaching_opening(req, opening.job_title):
            open_teaching += open_slots
        else:
            open_non_teaching += open_slots
    open_total = open_teaching + open_non_teaching

    dept_faculty: dict[str, int] = defaultdict(int)
    for rec in active_faculty:
        key = str(rec.department_id) if rec.department_id else "__none__"
        dept_faculty[key] += 1

    faculty_by_department: list[FacultyDepartmentCountItem] = []
    for dept in departments:
        count = dept_faculty.get(str(dept.id), 0)
        if count == 0 and dept_oid is not None and dept.id != dept_oid:
            continue
        faculty_by_department.append(
            FacultyDepartmentCountItem(
                department_id=str(dept.id),
                department_code=dept.department_code,
                department_name=dept.name,
                faculty_count=count,
            )
        )
    if dept_faculty.get("__none__"):
        faculty_by_department.append(
            FacultyDepartmentCountItem(
                department_id=None,
                department_code="—",
                department_name="Unassigned",
                faculty_count=dept_faculty["__none__"],
            )
        )
    faculty_by_department.sort(key=lambda x: x.faculty_count, reverse=True)

    join_window_start = anchor - timedelta(days=30)
    recent_employees = [
        e for e in employee_records if e.joining_date and join_window_start <= e.joining_date <= anchor and employee_row_matches(e)
    ]
    recent_employees.sort(key=lambda e: e.joining_date or date.min, reverse=True)

    user_ids = {e.user_id for e in recent_employees[:12]}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}

    recent_rows: list[RecentJoinerRow] = []
    for emp in recent_employees[:8]:
        user = user_by_id.get(emp.user_id)
        dept_name = None
        if emp.department_id and emp.department_id in dept_by_id:
            dept_name = dept_by_id[emp.department_id].name
        status_key, status_label = await _onboarding_status_label(
            tenant_id,
            emp.user_id,
            employment_status=emp.employment_status,
        )
        recent_rows.append(
            RecentJoinerRow(
                user_id=str(emp.user_id),
                full_name=user.full_name if user else "—",
                designation=emp.designation,
                department_name=dept_name,
                joined_on=emp.joining_date,
                onboarding_status=status_key,
                onboarding_label=status_label,
            )
        )

    qual_counts: dict[str, int] = defaultdict(int)
    for rec in active_faculty:
        profile = profile_by_user.get(rec.user_id)
        quals = rec.qualifications or (profile.qualifications if profile else [])
        bucket = _qualification_bucket(quals)
        if bucket:
            qual_counts[bucket] += 1

    desig_counts: dict[str, int] = defaultdict(int)
    for rec in active_faculty:
        bucket = _designation_bucket(rec.designation)
        if bucket:
            desig_counts[bucket] += 1
    desig_total = sum(desig_counts.values())
    designation_mix = [
        DistributionItem(
            key=key,
            label=label,
            count=desig_counts.get(key, 0),
            share_pct=round((desig_counts[key] / desig_total) * 100, 1) if desig_total else None,
        )
        for key, label in _DESIGNATION_BUCKETS
        if desig_counts.get(key, 0) > 0
    ]
    qualification_mix = _distribution(dict(qual_counts))

    workforce_ids: set[PydanticObjectId] = set()
    for rec in active_faculty:
        workforce_ids.add(rec.user_id)
    for emp in employee_records:
        if employee_row_matches(emp):
            workforce_ids.add(emp.user_id)

    attendance_rows = await HrEmployeeAttendanceRecord.find(
        Eq(HrEmployeeAttendanceRecord.tenant_id, tenant_id),
        Eq(HrEmployeeAttendanceRecord.attendance_date, anchor),
        In(HrEmployeeAttendanceRecord.employee_user_id, list(workforce_ids)),
    ).to_list() if workforce_ids else []
    att_by_user = {a.employee_user_id: a for a in attendance_rows}

    on_leave_users: set[PydanticObjectId] = set()
    for req in await LeaveRequest.find(
        Eq(LeaveRequest.tenant_id, tenant_id),
        Eq(LeaveRequest.status, LeaveRequestStatus.APPROVED),
    ).to_list():
        if req.start_date <= anchor <= req.end_date:
            if req.employee_user_id in workforce_ids:
                on_leave_users.add(req.employee_user_id)

    present = 0
    on_leave = 0
    not_checked_in = 0
    for uid in workforce_ids:
        if uid in on_leave_users:
            on_leave += 1
            continue
        row = att_by_user.get(uid)
        if row and row.status in _PRESENT_STATUSES:
            present += 1
        elif row and row.status == EmployeeAttendanceDayStatus.ON_LEAVE:
            on_leave += 1
        elif row is None or row.status in (
            EmployeeAttendanceDayStatus.ABSENT,
            EmployeeAttendanceDayStatus.MISSING,
            EmployeeAttendanceDayStatus.INCOMPLETE,
            EmployeeAttendanceDayStatus.MISSING_PUNCH,
        ):
            not_checked_in += 1
        else:
            present += 1

    availability = [
        AvailabilityOverviewItem(
            status_key="present",
            label="Present",
            description="Biometric check-in recorded for today",
            count=present,
        ),
        AvailabilityOverviewItem(
            status_key="on_leave",
            label="On approved leave",
            description="Casual, medical and on-duty",
            count=on_leave,
        ),
        AvailabilityOverviewItem(
            status_key="not_checked_in",
            label="Not yet checked in",
            description="No attendance mark recorded yet today",
            count=not_checked_in,
        ),
    ]

    designation_options = sorted(
        {
            d
            for d in (
                [_norm_designation(r.designation) for r in faculty_records]
                + [_norm_designation(e.designation) for e in employee_records]
            )
            if d
        }
    )

    return FacultyStatisticsOverviewRead(
        filters=FacultyStatisticsFilters(
            anchor_date=anchor,
            date_range=date_range,
            department_id=department_id,
            designation=designation,
            campus_id=campus_id,
        ),
        academic_term=AcademicTermSummary(academic_year_label=year, semester_label=semester),
        kpis=FacultyStatisticsKpiRead(
            teaching_faculty_total=teaching_total,
            teaching_faculty_regular=teaching_regular,
            teaching_faculty_visiting=teaching_visiting,
            non_teaching_staff_total=non_teaching,
            non_teaching_staff_detail="Admin, technical & support",
            student_faculty_ratio_display=ratio_display,
            student_faculty_ratio_students_per_faculty=ratio_value,
            regulatory_ratio_max=ratio_max,
            regulatory_ratio_label=ratio_label,
            regulatory_ratio_meets_norm=meets_norm,
            open_positions_total=open_total,
            open_positions_teaching=open_teaching,
            open_positions_non_teaching=open_non_teaching,
        ),
        faculty_by_department=faculty_by_department,
        recently_joined=recent_rows,
        recently_joined_count=len(recent_employees),
        recently_joined_window_days=30,
        qualification_mix=qualification_mix,
        designation_mix=designation_mix,
        availability_today=availability,
        availability_anchor_date=anchor,
        designation_filter_options=designation_options,
        generated_at=utcnow(),
    )