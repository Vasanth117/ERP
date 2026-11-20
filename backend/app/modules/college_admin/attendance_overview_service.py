"""College admin dashboard — attendance overview aggregates."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from statistics import mean

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.modules.academics.models import PendingAttendanceSubmission
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.modules.attendance.enums import AttendanceCorrectionStatus, AttendanceMarkStatus, AttendanceSessionStatus
from app.modules.attendance.models import AttendanceCorrectionRequest, AttendancePolicyReference, AttendanceRecord, AttendanceSession
from app.modules.attendance.policy_engine import calculate_percentage
from app.modules.college_admin.attendance_admin_models import AttendancePolicyAudience, InstitutionAttendancePolicy
from app.modules.college_admin.enums import DashboardDateRange
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus, FacultyRecord
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.models import InstitutionSettings
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AcademicTermSummary,
    AttendanceByYearItem,
    AttendanceCorrectionBucket,
    AttendanceDepartmentRow,
    AttendanceOverviewFilters,
    AttendanceOverviewKpiRead,
    AttendanceOverviewRead,
    AttendanceShortageAlert,
    DailyAttendancePoint,
)
from app.modules.college_admin.student_admin_models import StudentLifecycleStatus, StudentRecord
from app.modules.faculty.models import FacultyProfile
from app.modules.hr.attendance_schedule_models import HrEmployeeAttendanceRecord
from app.modules.hr.enums import EmployeeAttendanceDayStatus, LeaveRequestStatus
from app.modules.hr.models import LeaveRequest
from app.modules.students.models import StudentProfile

_reader = OperationalDataReader()

_ENROLLED = frozenset(
    {
        StudentLifecycleStatus.ADMITTED.value,
        StudentLifecycleStatus.ACTIVE.value,
        StudentLifecycleStatus.ON_LEAVE.value,
    }
)

_PRESENT_MARKS = frozenset(
    {AttendanceMarkStatus.PRESENT, AttendanceMarkStatus.LATE, AttendanceMarkStatus.EXCUSED}
)

_ACTIVE_EMPLOYMENT = frozenset(
    {
        FacultyEmploymentStatus.ACTIVE,
        FacultyEmploymentStatus.CONFIRMED,
        FacultyEmploymentStatus.PROBATION,
        FacultyEmploymentStatus.AWAITING_CONFIRMATION,
        FacultyEmploymentStatus.ON_LEAVE,
    }
)

_FACULTY_PRESENT = frozenset(
    {
        EmployeeAttendanceDayStatus.PRESENT,
        EmployeeAttendanceDayStatus.LATE,
        EmployeeAttendanceDayStatus.WORK_FROM_HOME,
        EmployeeAttendanceDayStatus.HALF_DAY,
        EmployeeAttendanceDayStatus.EARLY_DEPARTURE,
    }
)

_RANGE_LABELS = {
    DashboardDateRange.TODAY: "Today",
    DashboardDateRange.WEEK: "This week",
    DashboardDateRange.MONTH: "Last 30 days",
    DashboardDateRange.SEMESTER: "This semester",
}

_YEAR_BUCKETS: tuple[tuple[str, str], ...] = (
    ("year_1", "Year 1"),
    ("year_2", "Year 2"),
    ("year_3", "Year 3"),
    ("year_4", "Year 4"),
)


def _batch_start_year(batch_label: str | None) -> int | None:
    if not batch_label:
        return None
    match = re.match(r"^(\d{4})", batch_label.strip())
    return int(match.group(1)) if match else None


def _academic_year_start(academic_year_label: str | None) -> int | None:
    if not academic_year_label:
        return None
    match = re.match(r"^(\d{4})", academic_year_label.strip())
    return int(match.group(1)) if match else None


def _study_year(batch_label: str | None, academic_year_label: str | None) -> int | None:
    batch_start = _batch_start_year(batch_label)
    ay_start = _academic_year_start(academic_year_label)
    if batch_start is None or ay_start is None:
        return None
    return max(1, min(6, ay_start - batch_start + 1))


def _study_bucket(batch_label: str | None, ay_label: str | None) -> str:
    year = _study_year(batch_label, ay_label) or 1
    return f"year_{min(year, 4)}"


def _day_label(d: date) -> str:
    return f"{d.day} {d.strftime('%b')}"


async def _student_policy_rules(tenant_id: PydanticObjectId):
    inst = await InstitutionAttendancePolicy.find_one(
        Eq(InstitutionAttendancePolicy.tenant_id, tenant_id),
        Eq(InstitutionAttendancePolicy.audience, AttendancePolicyAudience.STUDENT),
        Eq(InstitutionAttendancePolicy.is_active, True),
    )
    if inst:
        return inst.rules
    ref = await AttendancePolicyReference.find_one(
        Eq(AttendancePolicyReference.tenant_id, tenant_id),
        Eq(AttendancePolicyReference.is_active, True),
    )
    return ref.rules if ref else None


def _policy_thresholds(settings: InstitutionSettings | None, rules) -> tuple[float, float, float]:
    raw = (settings.settings or {}) if settings else {}
    minimum = float(rules.min_percentage_required) if rules else float(raw.get("attendance_minimum_pct", 75))
    target = float(raw.get("attendance_semester_target_pct", 85))
    detention = float(raw.get("attendance_detention_threshold_pct", min(65.0, minimum - 10)))
    return target, minimum, detention


def _dept_status(
    *,
    today_pct: float | None,
    semester_pct: float | None,
    below_minimum: int,
) -> tuple[str, str]:
    if (semester_pct is not None and semester_pct < 75) or (today_pct is not None and today_pct < 75):
        return "at_risk", "At risk"
    if (
        (semester_pct is not None and semester_pct < 85)
        or (today_pct is not None and today_pct < 85)
        or below_minimum > 0
    ):
        return "monitor", "Monitor"
    return "healthy", "Healthy"


def _chart_dates(anchor: date, date_range: DashboardDateRange) -> list[date]:
    if date_range == DashboardDateRange.TODAY:
        return [anchor]
    if date_range == DashboardDateRange.WEEK:
        return [anchor - timedelta(days=i) for i in range(6, -1, -1)]
    if date_range == DashboardDateRange.MONTH:
        return [anchor - timedelta(days=i) for i in range(29, -1, -1)]
    return [anchor]


def _is_teaching_employee(employment_type: str | None, designation: str | None) -> bool:
    blob = f"{employment_type or ''} {designation or ''}".lower()
    if any(k in blob for k in ("non-teaching", "admin", "accounts", "support staff", "clerical")):
        return False
    return any(k in blob for k in ("faculty", "professor", "lecturer", "teaching", "academic"))


async def get_attendance_overview(
    scope: AccessScope,
    *,
    anchor_date: date | None = None,
    date_range: DashboardDateRange = DashboardDateRange.MONTH,
    department_id: str | None = None,
    programme_code: str | None = None,
    campus_id: str | None = None,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> AttendanceOverviewRead:
    authorize(scope, Permission.COLLEGE_DASHBOARD_READ)
    tenant_id = require_college_tenant_scope(scope)
    anchor = anchor_date or date.today()
    dept_oid = to_object_id(department_id, "department_id") if department_id else None
    campus_oid = to_object_id(campus_id, "campus_id") if campus_id else None
    prog_filter = programme_code.upper() if programme_code else None

    year, semester = await _reader.current_academic_term(tenant_id)
    ay_label = academic_year_label or year
    sem_label = semester_label or semester

    rules = await _student_policy_rules(tenant_id)
    inst_settings = await InstitutionSettings.find_one(Eq(InstitutionSettings.tenant_id, tenant_id))
    target_pct, minimum_pct, detention_pct = _policy_thresholds(inst_settings, rules)

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    if dept_oid:
        departments = [d for d in departments if d.id == dept_oid]
    campus_dept_ids: set[PydanticObjectId] | None = None
    if campus_oid is not None:
        campus_dept_ids = {d.id for d in departments if campus_oid in d.campus_ids}

    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    profile_by_user = {p.user_id: p for p in profiles}
    records = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).to_list()

    enrolled: list[dict] = []
    seen: set[PydanticObjectId] = set()

    def row_matches(*, department_id: PydanticObjectId | None, programme_code: str | None) -> bool:
        if dept_oid and department_id != dept_oid:
            return False
        if campus_dept_ids is not None and department_id and department_id not in campus_dept_ids:
            return False
        if prog_filter and (programme_code or "").upper() != prog_filter:
            return False
        return True

    for record in records:
        if record.lifecycle_status.value not in _ENROLLED:
            continue
        dept_id = record.department_id or (profile_by_user.get(record.user_id).department_id if profile_by_user.get(record.user_id) else None)
        if not row_matches(department_id=dept_id, programme_code=record.programme_code):
            continue
        seen.add(record.user_id)
        profile = profile_by_user.get(record.user_id)
        enrolled.append(
            {
                "user_id": record.user_id,
                "department_id": dept_id,
                "programme_code": record.programme_code,
                "batch_label": record.batch_label or (profile.batch_label if profile else None),
            }
        )

    for profile in profiles:
        if profile.user_id in seen:
            continue
        if not row_matches(department_id=profile.department_id, programme_code=profile.programme_code):
            continue
        enrolled.append(
            {
                "user_id": profile.user_id,
                "department_id": profile.department_id,
                "programme_code": profile.programme_code,
                "batch_label": profile.batch_label,
            }
        )

    enrolled_ids = {row["user_id"] for row in enrolled}
    user_dept = {row["user_id"]: str(row["department_id"]) if row["department_id"] else None for row in enrolled}

    sessions = await AttendanceSession.find(
        Eq(AttendanceSession.tenant_id, tenant_id),
        Eq(AttendanceSession.status, AttendanceSessionStatus.SUBMITTED),
    ).to_list()
    if ay_label:
        sessions = [s for s in sessions if s.academic_year_label == ay_label]
    if sem_label:
        sessions = [s for s in sessions if s.semester_label == sem_label]
    session_ids = {s.id for s in sessions}
    sessions_by_date: dict[date, list[AttendanceSession]] = defaultdict(list)
    for s in sessions:
        sessions_by_date[s.session_date].append(s)

    records_by_student: dict[PydanticObjectId, list[AttendanceRecord]] = defaultdict(list)
    records_by_student_date: dict[tuple[PydanticObjectId, date], list[AttendanceRecord]] = defaultdict(list)
    if session_ids:
        att_records = await AttendanceRecord.find(
            Eq(AttendanceRecord.tenant_id, tenant_id),
            In(AttendanceRecord.session_id, list(session_ids)),
        ).to_list()
        session_map = {s.id: s for s in sessions}
        for rec in att_records:
            if rec.student_user_id not in enrolled_ids:
                continue
            session = session_map.get(rec.session_id)
            if session is None:
                continue
            records_by_student[rec.student_user_id].append(rec)
            records_by_student_date[(rec.student_user_id, session.session_date)].append(rec)

    student_semester_pct: dict[PydanticObjectId, float] = {}
    for uid in enrolled_ids:
        recs = records_by_student.get(uid, [])
        if rules and recs:
            student_semester_pct[uid] = calculate_percentage(recs, rules)
        elif recs:
            present = sum(1 for r in recs if r.status in _PRESENT_MARKS)
            student_semester_pct[uid] = round((present / len(recs)) * 100, 2)

    semester_values = [
        student_semester_pct[uid] for uid in enrolled_ids if records_by_student.get(uid)
    ]
    semester_avg = round(mean(semester_values), 1) if semester_values else None
    below_minimum = sum(
        1 for uid in enrolled_ids if uid in student_semester_pct and student_semester_pct[uid] < minimum_pct
    )

    today_sessions = sessions_by_date.get(anchor, [])
    today_session_ids = {s.id for s in today_sessions}
    present_today: set[PydanticObjectId] = set()
    if today_session_ids:
        for uid in enrolled_ids:
            day_recs = records_by_student_date.get((uid, anchor), [])
            if not day_recs:
                continue
            if any(r.status in _PRESENT_MARKS for r in day_recs):
                present_today.add(uid)
    today_total = len(enrolled_ids)
    today_present = len(present_today)
    today_pct = round((today_present / today_total) * 100, 1) if today_total else None

    chart_days = _chart_dates(anchor, date_range)
    if date_range == DashboardDateRange.SEMESTER:
        chart_days = sorted(sessions_by_date.keys()) or [anchor]

    daily_points: list[DailyAttendancePoint] = []
    for day in chart_days:
        if day > anchor:
            continue
        day_present = 0
        for uid in enrolled_ids:
            day_recs = records_by_student_date.get((uid, day), [])
            if day_recs and any(r.status in _PRESENT_MARKS for r in day_recs):
                day_present += 1
        day_total = today_total
        day_pct = round((day_present / day_total) * 100, 1) if day_total else None
        daily_points.append(
            DailyAttendancePoint(
                label=_day_label(day),
                session_date=day,
                attendance_pct=day_pct,
                students_present=day_present,
                students_total=day_total,
            )
        )

    dept_meta = {str(d.id): d for d in departments}
    dept_students: dict[str, list[PydanticObjectId]] = defaultdict(list)
    for row in enrolled:
        key = str(row["department_id"]) if row["department_id"] else "_none"
        if key == "_none":
            continue
        dept_students[key].append(row["user_id"])

    department_rows: list[AttendanceDepartmentRow] = []
    for did, students in dept_students.items():
        dept = dept_meta.get(did)
        if dept is None:
            continue
        dept_present_today = sum(1 for uid in students if uid in present_today)
        dept_today_pct = round((dept_present_today / len(students)) * 100, 1) if students else None
        dept_sem = [student_semester_pct[uid] for uid in students if records_by_student.get(uid)]
        dept_sem_avg = round(mean(dept_sem), 1) if dept_sem else None
        dept_below = sum(
            1 for uid in students if uid in student_semester_pct and student_semester_pct[uid] < minimum_pct
        )
        status_key, status_label = _dept_status(
            today_pct=dept_today_pct,
            semester_pct=dept_sem_avg,
            below_minimum=dept_below,
        )
        department_rows.append(
            AttendanceDepartmentRow(
                department_id=did,
                department_code=dept.department_code,
                department_name=dept.name,
                student_count=len(students),
                today_pct=dept_today_pct,
                semester_avg_pct=dept_sem_avg,
                below_minimum_count=dept_below,
                status_key=status_key,
                status_label=status_label,
            )
        )
    department_rows.sort(key=lambda r: (-(r.today_pct or 0), r.department_name))
    dept_limit = 8
    dept_visible = department_rows[:dept_limit]

    year_buckets: dict[str, list[float]] = defaultdict(list)
    year_counts: dict[str, int] = defaultdict(int)
    for row in enrolled:
        bucket = _study_bucket(row["batch_label"], ay_label)
        if not bucket.startswith("year_"):
            continue
        year_counts[bucket] += 1
        if records_by_student.get(row["user_id"]):
            year_buckets[bucket].append(student_semester_pct[row["user_id"]])
    attendance_by_year = [
        AttendanceByYearItem(
            bucket_key=key,
            label=label,
            attendance_pct=round(mean(year_buckets[key]), 1) if year_buckets[key] else None,
            student_count=year_counts.get(key, 0),
        )
        for key, label in _YEAR_BUCKETS
        if year_counts.get(key, 0) > 0 or year_buckets.get(key)
    ]

    pending_corrections = await AttendanceCorrectionRequest.find(
        Eq(AttendanceCorrectionRequest.tenant_id, tenant_id),
        Eq(AttendanceCorrectionRequest.status, AttendanceCorrectionStatus.PENDING),
    ).count()
    week_start = datetime.combine(anchor - timedelta(days=anchor.weekday()), datetime.min.time(), tzinfo=timezone.utc)
    approved_week = await AttendanceCorrectionRequest.find(
        Eq(AttendanceCorrectionRequest.tenant_id, tenant_id),
        Eq(AttendanceCorrectionRequest.status, AttendanceCorrectionStatus.APPROVED),
    ).to_list()
    approved_week_count = sum(
        1 for r in approved_week if r.resolved_at and r.resolved_at >= week_start
    )
    pending_submissions = await PendingAttendanceSubmission.find(
        Eq(PendingAttendanceSubmission.tenant_id, tenant_id),
    ).count()
    correction_requests = [
        AttendanceCorrectionBucket(bucket_key="pending_review", label="Pending review", count=pending_corrections),
        AttendanceCorrectionBucket(
            bucket_key="awaiting_hod",
            label="Awaiting HoD approval",
            count=pending_submissions,
        ),
        AttendanceCorrectionBucket(
            bucket_key="approved_week",
            label="Approved this week",
            count=approved_week_count,
        ),
    ]

    detention_count = sum(
        1 for uid in enrolled_ids if uid in student_semester_pct and student_semester_pct[uid] < detention_pct
    )
    condonation_count = sum(
        1
        for uid in enrolled_ids
        if uid in student_semester_pct and detention_pct <= student_semester_pct[uid] < minimum_pct
    )
    shortage_alerts = [
        AttendanceShortageAlert(
            alert_key="detention_risk",
            label=f"Below {detention_pct:g}% – detention risk",
            count=detention_count,
        ),
        AttendanceShortageAlert(
            alert_key="condonation_band",
            label=f"{detention_pct:g}–{minimum_pct:g}% – condonation band",
            count=condonation_count,
        ),
    ]

    faculty_records = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    employee_records = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    faculty_profiles = await FacultyProfile.find(Eq(FacultyProfile.tenant_id, tenant_id)).to_list()
    profile_by_faculty = {p.user_id: p for p in faculty_profiles}
    workforce: set[PydanticObjectId] = set()
    for rec in faculty_records:
        if rec.employment_status not in _ACTIVE_EMPLOYMENT:
            continue
        profile = profile_by_faculty.get(rec.user_id)
        if dept_oid and profile and profile.department_id != dept_oid:
            continue
        workforce.add(rec.user_id)
    for emp in employee_records:
        if emp.employment_status not in _ACTIVE_EMPLOYMENT:
            continue
        if not _is_teaching_employee(emp.employment_type, emp.designation):
            continue
        if dept_oid and emp.department_id != dept_oid:
            continue
        workforce.add(emp.user_id)

    attendance_rows = (
        await HrEmployeeAttendanceRecord.find(
            Eq(HrEmployeeAttendanceRecord.tenant_id, tenant_id),
            Eq(HrEmployeeAttendanceRecord.attendance_date, anchor),
            In(HrEmployeeAttendanceRecord.employee_user_id, list(workforce)),
        ).to_list()
        if workforce
        else []
    )
    att_by_user = {a.employee_user_id: a for a in attendance_rows}
    on_leave_users: set[PydanticObjectId] = set()
    for req in await LeaveRequest.find(
        Eq(LeaveRequest.tenant_id, tenant_id),
        Eq(LeaveRequest.status, LeaveRequestStatus.APPROVED),
    ).to_list():
        if req.start_date <= anchor <= req.end_date and req.employee_user_id in workforce:
            on_leave_users.add(req.employee_user_id)

    faculty_present = 0
    for uid in workforce:
        if uid in on_leave_users:
            continue
        row = att_by_user.get(uid)
        if row and row.status in _FACULTY_PRESENT:
            faculty_present += 1
        elif row and row.status == EmployeeAttendanceDayStatus.ON_LEAVE:
            continue
        elif row is None:
            continue
        else:
            if row.status not in (
                EmployeeAttendanceDayStatus.ABSENT,
                EmployeeAttendanceDayStatus.MISSING,
                EmployeeAttendanceDayStatus.INCOMPLETE,
                EmployeeAttendanceDayStatus.MISSING_PUNCH,
            ):
                faculty_present += 1

    faculty_total = len(workforce)
    faculty_pct = round((faculty_present / faculty_total) * 100, 1) if faculty_total else None

    return AttendanceOverviewRead(
        filters=AttendanceOverviewFilters(
            anchor_date=anchor,
            date_range=date_range,
            department_id=department_id,
            programme_code=programme_code,
            campus_id=campus_id,
            academic_year_label=ay_label,
            semester_label=sem_label,
        ),
        academic_term=AcademicTermSummary(academic_year_label=ay_label, semester_label=sem_label),
        range_display_label=_RANGE_LABELS.get(date_range),
        kpis=AttendanceOverviewKpiRead(
            today_student_attendance_pct=today_pct,
            today_students_present=today_present,
            today_students_total=today_total,
            semester_average_pct=semester_avg,
            semester_target_pct=target_pct,
            semester_minimum_pct=minimum_pct,
            students_below_minimum=below_minimum,
            today_faculty_attendance_pct=faculty_pct,
            today_faculty_present=faculty_present,
            today_faculty_total=faculty_total,
        ),
        daily_student_attendance=daily_points,
        department_rows=dept_visible,
        department_rows_total=len(department_rows),
        department_rows_limit=dept_limit,
        attendance_by_year=attendance_by_year,
        correction_requests=correction_requests,
        shortage_alerts=shortage_alerts,
        generated_at=utcnow(),
    )