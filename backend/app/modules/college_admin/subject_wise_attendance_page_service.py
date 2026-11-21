"""Subject-wise student attendance (CA 08.04)."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from statistics import mean
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.academics.curriculum_models import CourseRecord
from app.modules.attendance.enums import AttendanceMarkStatus, AttendanceSessionStatus
from app.modules.attendance.models import AttendanceRecord, AttendanceSession
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicYear
from app.modules.college_admin.attendance_dashboard_page_service import _parse_term_key, _term_key, _term_label
from app.modules.college_admin.attendance_overview_service import (
    _PRESENT_MARKS,
    _policy_thresholds,
    _student_policy_rules,
)
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.models import InstitutionSettings
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    StudentAdminDashboardFilterOption,
    SubjectWiseAttendancePageRead,
    SubjectWiseAttendanceRow,
)

_IST = ZoneInfo("Asia/Kolkata")
_reader = OperationalDataReader()
_TABLE_LIMIT = 20


def _fmt_time_label(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Updated %H:%M IST")


def _fmt_snapshot(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Snapshot · %d %b %Y, %H:%M IST")


def _parse_scope_key(scope_key: str | None) -> tuple[str | None, int | None]:
    if not scope_key or "|" not in scope_key:
        return None, None
    dept_code, sem_raw = scope_key.split("|", 1)
    try:
        sem = int(sem_raw.strip())
    except ValueError:
        sem = None
    return (dept_code.strip().upper() or None), sem


def _scope_key(dept_code: str, semester_number: int) -> str:
    return f"{dept_code.upper()}|{semester_number}"


async def get_subject_wise_attendance_page(
    scope: AccessScope,
    *,
    term_key: str | None = None,
    scope_key: str | None = None,
) -> SubjectWiseAttendancePageRead:
    authorize(scope, Permission.ATTENDANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    ay_override, sem_override = _parse_term_key(term_key)
    current_ay, current_sem = await _reader.current_academic_term(tenant_id)
    ay_label = ay_override or current_ay
    sem_label = sem_override or current_sem

    dept_code_filter, sem_num_filter = _parse_scope_key(scope_key)

    rules = await _student_policy_rules(tenant_id)
    inst_settings = await InstitutionSettings.find_one(Eq(InstitutionSettings.tenant_id, tenant_id))
    _target_pct, minimum_pct, _detention_pct = _policy_thresholds(inst_settings, rules)

    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-year_code").to_list()
    term_options: list[StudentAdminDashboardFilterOption] = []
    for y in years:
        label = _term_label(sem_label if y.is_current else current_sem, y.year_code)
        term_options.append(
            StudentAdminDashboardFilterOption(
                value=_term_key(y.year_code, sem_label if y.is_current else current_sem),
                label=label,
            ),
        )
    if not term_options and ay_label:
        term_options = [
            StudentAdminDashboardFilterOption(value=_term_key(ay_label, sem_label), label=_term_label(sem_label, ay_label))
        ]

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    dept_by_id = {d.id: d for d in departments}
    courses = await CourseRecord.find(Eq(CourseRecord.tenant_id, tenant_id), Eq(CourseRecord.is_active, True)).to_list()
    course_by_code = {(c.course_code or "").upper(): c for c in courses if c.course_code}

    scope_options = [StudentAdminDashboardFilterOption(value="", label="All scopes")]
    seen_scopes: set[str] = set()
    for course in courses:
        dept = dept_by_id.get(course.department_id) if course.department_id else None
        if not dept or not dept.department_code or course.semester_number is None:
            continue
        key = _scope_key(dept.department_code, course.semester_number)
        if key in seen_scopes:
            continue
        seen_scopes.add(key)
        scope_options.append(
            StudentAdminDashboardFilterOption(
                value=key,
                label=f"{dept.department_code} - Sem {course.semester_number}",
            ),
        )

    sessions = await AttendanceSession.find(
        Eq(AttendanceSession.tenant_id, tenant_id),
        Eq(AttendanceSession.status, AttendanceSessionStatus.SUBMITTED),
    ).to_list()
    if ay_label:
        sessions = [s for s in sessions if s.academic_year_label == ay_label]
    if sem_label:
        sessions = [s for s in sessions if s.semester_label == sem_label]

    def session_matches(course: CourseRecord | None) -> bool:
        if not dept_code_filter and sem_num_filter is None:
            return True
        if course is None:
            return False
        dept = dept_by_id.get(course.department_id) if course.department_id else None
        if dept_code_filter and (not dept or (dept.department_code or "").upper() != dept_code_filter):
            return False
        if sem_num_filter is not None and course.semester_number != sem_num_filter:
            return False
        return True

    sessions_by_course: dict[str, list[AttendanceSession]] = defaultdict(list)
    for session in sessions:
        code = (session.course_code or "").upper()
        course = course_by_code.get(code)
        if not session_matches(course):
            continue
        sessions_by_course[code].append(session)

    session_ids = [s.id for s in sessions if (s.course_code or "").upper() in sessions_by_course]
    records_by_session: dict[PydanticObjectId, list[AttendanceRecord]] = defaultdict(list)
    if session_ids:
        for rec in await AttendanceRecord.find(
            Eq(AttendanceRecord.tenant_id, tenant_id),
            In(AttendanceRecord.session_id, session_ids),
        ).to_list():
            records_by_session[rec.session_id].append(rec)

    faculty_ids: set[PydanticObjectId] = set()
    for sess_list in sessions_by_course.values():
        for s in sess_list:
            faculty_ids.add(s.faculty_user_id)
    faculty_names: dict[PydanticObjectId, str] = {}
    if faculty_ids:
        for user in await User.find(In(User.id, list(faculty_ids))).to_list():
            faculty_names[user.id] = user.full_name or user.email or "—"

    subject_rows: list[SubjectWiseAttendanceRow] = []
    for code, sess_list in sessions_by_course.items():
        course = course_by_code.get(code)
        session_rates: list[float] = []
        student_presence: dict[PydanticObjectId, tuple[int, int]] = defaultdict(lambda: (0, 0))

        for session in sess_list:
            recs = records_by_session.get(session.id, [])
            if not recs:
                continue
            present = sum(1 for r in recs if r.status in _PRESENT_MARKS)
            session_rates.append(round((present / len(recs)) * 100, 1))
            for rec in recs:
                p, t = student_presence[rec.student_user_id]
                if rec.status in _PRESENT_MARKS:
                    student_presence[rec.student_user_id] = (p + 1, t + 1)
                else:
                    student_presence[rec.student_user_id] = (p, t + 1)

        student_pcts = [
            round((p / t) * 100, 1) for p, t in student_presence.values() if t > 0
        ]
        avg = round(mean(session_rates), 0) if session_rates else None
        if avg is None and student_pcts:
            avg = round(mean(student_pcts), 0)
        below = sum(1 for pct in student_pcts if pct < minimum_pct)

        faculty_counter = Counter(s.faculty_user_id for s in sess_list)
        primary_faculty = faculty_counter.most_common(1)[0][0] if faculty_counter else None
        faculty_label = faculty_names.get(primary_faculty, "—") if primary_faculty else "—"

        subject_rows.append(
            SubjectWiseAttendanceRow(
                subject_name=course.name if course else code,
                subject_code=code,
                faculty_label=faculty_label,
                classes_held=len(sess_list),
                average_pct=avg,
                below_minimum_count=below,
            ),
        )

    subject_rows.sort(key=lambda r: (-r.classes_held, r.subject_name))
    total = len(subject_rows)
    visible = subject_rows[:_TABLE_LIMIT]

    return SubjectWiseAttendancePageRead(
        page_title="Subject-wise Attendance",
        page_subtitle="Class attendance by subject",
        export_label="Export",
        term_filter_label="Academic term",
        scope_filter_label="Programme scope",
        scope_indicator_label="College scope",
        updated_at_label=_fmt_time_label(now),
        term_options=term_options,
        scope_options=scope_options,
        selected_term_key=_term_key(ay_label, sem_label),
        selected_scope_key=scope_key or "",
        subjects_table_title="Subjects",
        subjects_table_headers=["Subject", "Code", "Faculty", "Classes held", "Average", f"Below {minimum_pct:g}%"],
        subject_rows=visible,
        subjects_footer_label=f"Showing {len(visible)} of {total}",
        footer_disclaimer="Live institutional data · Student attendance · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )