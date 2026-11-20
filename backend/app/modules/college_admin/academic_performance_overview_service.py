"""Academic performance analytics for college admin dashboard."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from statistics import mean

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.common.access import AccessScope
from app.common.time import utcnow
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.modules.attendance.enums import AttendanceMarkStatus, AttendanceSessionStatus
from app.modules.attendance.models import AttendanceRecord, AttendanceSession
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.models import InstitutionSettings
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AcademicPerformanceFilters,
    AcademicPerformanceKpiRead,
    AcademicPerformanceOverviewRead,
    AcademicRiskItem,
    AcademicTermSummary,
    GradeDistributionItem,
    LowPassSubjectRow,
    PassRateByStudyYearBar,
    PassRateTrendPoint,
    TopPerformerRow,
)
from app.modules.examinations.exam_cell_grading_enums import ExamSubjectResultOutcome
from app.modules.examinations.exam_cell_grading_models import ExamSemesterResult, ExamStudentSubjectResult
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.students.arrear_backlog_enums import BacklogStatus
from app.modules.students.arrear_backlog_models import StudentArrearReference
from app.modules.students.models import StudentProfile

_reader = OperationalDataReader()

_ATTENDANCE_PRESENT = frozenset(
    {AttendanceMarkStatus.PRESENT, AttendanceMarkStatus.LATE, AttendanceMarkStatus.EXCUSED}
)

_DISTINCTION_GRADES = frozenset({"O", "A+", "A", "S"})
_GRADE_LABELS = {
    "O": "O (Outstanding)",
    "A+": "A+ (Excellent)",
    "A": "A (Very good)",
    "B+": "B+ (Good)",
    "B": "B (Above average)",
    "C": "C (Average)",
    "P": "P (Pass)",
    "F": "F (Fail)",
}

_STUDY_YEAR_BUCKETS: tuple[tuple[str, str], ...] = (
    ("year_1", "Year 1"),
    ("year_2", "Year 2"),
    ("year_3", "Year 3"),
    ("year_4", "Year 4"),
    ("pg_1", "PG Year 1"),
    ("pg_2", "PG Year 2"),
)


def _batch_start_year(batch_label: str | None) -> int | None:
    if not batch_label:
        return None
    match = re.search(r"(20\d{2})", batch_label)
    return int(match.group(1)) if match else None


def _academic_year_start(label: str | None) -> int | None:
    if not label:
        return None
    match = re.match(r"^(\d{4})", label.strip())
    return int(match.group(1)) if match else None


def _study_year(batch_label: str | None, academic_year_label: str | None) -> int | None:
    batch_start = _batch_start_year(batch_label)
    ay_start = _academic_year_start(academic_year_label)
    if batch_start is None or ay_start is None:
        return None
    return max(1, min(6, ay_start - batch_start + 1))


def _programme_level(prog: AcademicProgramme) -> str:
    if prog.duration_semesters <= 4 and prog.credits_required <= 80:
        return "doctoral"
    if prog.duration_semesters <= 6:
        return "postgraduate"
    return "undergraduate"


def _study_bucket(batch_label: str | None, programme_code: str | None, prog_by_code: dict, ay_label: str | None) -> str:
    prog = prog_by_code.get((programme_code or "").upper())
    level = _programme_level(prog) if prog else "undergraduate"
    year = _study_year(batch_label, ay_label) or 1
    if level == "postgraduate" or level == "doctoral":
        if year <= 1:
            return "pg_1"
        return "pg_2"
    return f"year_{min(year, 4)}"


def _trend_label(session: ExamSession) -> str:
    year_bit = session.academic_year_label.split("-")[0] if session.academic_year_label else ""
    return f"{session.semester_label} {year_bit}".strip()


def _pass_rate(results: list[ExamStudentSubjectResult]) -> float | None:
    if not results:
        return None
    passed = sum(1 for r in results if r.outcome == ExamSubjectResultOutcome.PASS)
    return round((passed / len(results)) * 100, 1)


def _benchmark_for_label(settings: InstitutionSettings | None, trend_label: str) -> float | None:
    if settings is None:
        return None
    raw = settings.settings or {}
    by_sem = raw.get("university_pass_rate_by_semester")
    if isinstance(by_sem, dict) and trend_label in by_sem:
        val = by_sem[trend_label]
        return float(val) if isinstance(val, (int, float)) else None
    val = raw.get("university_pass_rate_benchmark")
    return float(val) if isinstance(val, (int, float)) else None


def _profile_matches(
    profile: StudentProfile,
    *,
    programme_code: str | None,
    study_year: int | None,
    ay_label: str | None,
    prog_by_code: dict,
) -> bool:
    if programme_code and (profile.programme_code or "").upper() != programme_code.upper():
        return False
    if study_year is not None:
        computed = _study_year(profile.batch_label, ay_label)
        if computed is None or computed != study_year:
            return False
    return True


async def get_academic_performance_overview(
    scope: AccessScope,
    *,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    programme_code: str | None = None,
    study_year: int | None = None,
) -> AcademicPerformanceOverviewRead:
    authorize(scope, Permission.COLLEGE_DASHBOARD_READ)
    tenant_id = require_college_tenant_scope(scope)

    year, semester = await _reader.current_academic_term(tenant_id)
    ay_label = academic_year_label or year
    sem_label = semester_label or semester

    settings = await InstitutionSettings.find_one(Eq(InstitutionSettings.tenant_id, tenant_id))
    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    prog_by_code = {p.programme_code.upper(): p for p in programmes if p.programme_code}

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    dept_by_id = {d.id: d for d in departments}

    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    filtered_profiles = [
        p
        for p in profiles
        if _profile_matches(
            p,
            programme_code=programme_code,
            study_year=study_year,
            ay_label=ay_label,
            prog_by_code=prog_by_code,
        )
    ]
    user_ids = {p.user_id for p in filtered_profiles}
    profile_by_user = {p.user_id: p for p in filtered_profiles}

    all_sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).to_list()
    all_sessions.sort(key=lambda s: (s.academic_year_label or "", s.semester_label or "", s.examination_end_at or s.created_at))

    def session_matches(s: ExamSession) -> bool:
        if ay_label and s.academic_year_label != ay_label:
            return False
        if sem_label and s.semester_label != sem_label:
            return False
        return True

    current_sessions = [s for s in all_sessions if session_matches(s)]
    current_session_ids = [s.id for s in current_sessions]

    current_results: list[ExamStudentSubjectResult] = []
    if current_session_ids:
        current_results = await ExamStudentSubjectResult.find(
            Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
            In(ExamStudentSubjectResult.exam_session_id, current_session_ids),
        ).to_list()
    current_results = [r for r in current_results if r.student_user_id in user_ids or not user_ids]

    overall_pass = _pass_rate(current_results)

    prev_sessions = [s for s in all_sessions if not session_matches(s)]
    prev_session = prev_sessions[-1] if prev_sessions else None
    prev_pass = None
    prev_label = None
    if prev_session:
        prev_label = _trend_label(prev_session)
        prev_rows = await ExamStudentSubjectResult.find(
            Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
            Eq(ExamStudentSubjectResult.exam_session_id, prev_session.id),
        ).to_list()
        prev_rows = [r for r in prev_rows if r.student_user_id in user_ids or not user_ids]
        prev_pass = _pass_rate(prev_rows)

    change_pts = None
    if overall_pass is not None and prev_pass is not None:
        change_pts = round(overall_pass - prev_pass, 1)

    semester_results = await ExamSemesterResult.find(
        Eq(ExamSemesterResult.tenant_id, tenant_id),
    ).to_list()
    if current_session_ids:
        semester_results = [r for r in semester_results if r.exam_session_id in current_session_ids]
    semester_results = [r for r in semester_results if r.student_user_id in user_ids]

    cgpas = [float(r.cgpa) for r in semester_results if r.cgpa is not None]
    avg_cgpa = round(mean(cgpas), 2) if cgpas else None

    ug_cgpas: list[float] = []
    pg_cgpas: list[float] = []
    for row in semester_results:
        if row.cgpa is None:
            continue
        profile = profile_by_user.get(row.student_user_id)
        prog = prog_by_code.get((profile.programme_code if profile else row.programme_code or "").upper())
        if prog and _programme_level(prog) in ("postgraduate", "doctoral"):
            pg_cgpas.append(float(row.cgpa))
        else:
            ug_cgpas.append(float(row.cgpa))

    distinction_students: set[PydanticObjectId] = set()
    for row in current_results:
        if row.grade_letter and row.grade_letter.upper() in _DISTINCTION_GRADES:
            distinction_students.add(row.student_user_id)
        elif row.grade_point is not None and row.grade_point >= 8.5:
            distinction_students.add(row.student_user_id)

    enrolled = len(filtered_profiles) if filtered_profiles else len(profiles)
    distinction_pct = round((len(distinction_students) / enrolled) * 100, 1) if enrolled else None

    arrears = await StudentArrearReference.find(
        Eq(StudentArrearReference.tenant_id, tenant_id),
        Eq(StudentArrearReference.backlog_status, BacklogStatus.PENDING),
    ).to_list()
    arrears = [a for a in arrears if a.user_id in user_ids or not user_ids]
    backlog_users = {a.user_id for a in arrears}
    arrears_by_user: Counter[PydanticObjectId] = Counter(a.user_id for a in arrears)
    three_plus = sum(1 for _, c in arrears_by_user.items() if c >= 3)
    backlog_pct = round((len(backlog_users) / enrolled) * 100, 1) if enrolled else None

    trend_points: list[PassRateTrendPoint] = []
    for session in all_sessions[-8:]:
        label = _trend_label(session)
        rows = await ExamStudentSubjectResult.find(
            Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
            Eq(ExamStudentSubjectResult.exam_session_id, session.id),
        ).to_list()
        rows = [r for r in rows if r.student_user_id in user_ids or not user_ids]
        trend_points.append(
            PassRateTrendPoint(
                label=label,
                college_pass_rate_pct=_pass_rate(rows),
                university_benchmark_pct=_benchmark_for_label(settings, label),
            )
        )

    bucket_stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for row in current_results:
        profile = profile_by_user.get(row.student_user_id)
        bucket = _study_bucket(
            profile.batch_label if profile else None,
            profile.programme_code if profile else None,
            prog_by_code,
            ay_label,
        )
        if row.outcome == ExamSubjectResultOutcome.PASS:
            bucket_stats[bucket][0] += 1
        else:
            bucket_stats[bucket][1] += 1

    study_year_bars = []
    for key, label in _STUDY_YEAR_BUCKETS:
        passed, failed = bucket_stats.get(key, [0, 0])
        total = passed + failed
        if total == 0 and not current_results:
            study_year_bars.append(PassRateByStudyYearBar(bucket_key=key, label=label, pass_rate_pct=None, student_count=0))
            continue
        if total == 0:
            continue
        study_year_bars.append(
            PassRateByStudyYearBar(
                bucket_key=key,
                label=label,
                pass_rate_pct=round((passed / total) * 100, 1),
                student_count=total,
            )
        )

    course_stats: dict[str, dict] = defaultdict(lambda: {"pass": 0, "fail": 0, "dept_ids": [], "name": None})
    for row in current_results:
        stats = course_stats[row.course_code]
        if row.outcome == ExamSubjectResultOutcome.PASS:
            stats["pass"] += 1
        else:
            stats["fail"] += 1
        profile = profile_by_user.get(row.student_user_id)
        if profile and profile.department_id:
            stats["dept_ids"].append(profile.department_id)
        if not stats["name"]:
            stats["name"] = row.course_code

    prev_by_course: dict[str, float | None] = {}
    if prev_session:
        prev_course = await ExamStudentSubjectResult.find(
            Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
            Eq(ExamStudentSubjectResult.exam_session_id, prev_session.id),
        ).to_list()
        prev_group: dict[str, list[ExamStudentSubjectResult]] = defaultdict(list)
        for r in prev_course:
            prev_group[r.course_code].append(r)
        for code, rows in prev_group.items():
            prev_by_course[code] = _pass_rate(rows)

    low_subjects: list[LowPassSubjectRow] = []
    for code, stats in course_stats.items():
        total = stats["pass"] + stats["fail"]
        if total == 0:
            continue
        rate = round((stats["pass"] / total) * 100, 1)
        if rate >= 80:
            continue
        dept_id = Counter(stats["dept_ids"]).most_common(1)[0][0] if stats["dept_ids"] else None
        dept = dept_by_id.get(dept_id) if dept_id else None
        prev_rate = prev_by_course.get(code)
        trend_key = "stable"
        trend_label = "Stable"
        if prev_rate is not None:
            if rate < prev_rate - 2:
                trend_key, trend_label = "declining", "Declining"
            elif rate > prev_rate + 2:
                trend_key, trend_label = "improving", "Improving"
        low_subjects.append(
            LowPassSubjectRow(
                course_code=code,
                course_name=stats["name"],
                department_code=dept.department_code if dept else None,
                department_name=dept.name if dept else None,
                semester_label=sem_label,
                appeared_count=total,
                pass_rate_pct=rate,
                trend_key=trend_key,
                trend_label=trend_label,
            )
        )
    low_subjects.sort(key=lambda r: (r.pass_rate_pct or 0, -r.appeared_count))

    grade_counts: Counter[str] = Counter()
    for row in current_results:
        if row.grade_letter:
            grade_counts[row.grade_letter.upper()] += 1
    grade_total = sum(grade_counts.values())
    grade_distribution = [
        GradeDistributionItem(
            key=letter,
            grade_letter=letter,
            label=_GRADE_LABELS.get(letter, letter),
            count=count,
            share_pct=round((count / grade_total) * 100, 1) if grade_total else None,
        )
        for letter, count in grade_counts.most_common()
    ]

    low_cgpa_count = sum(1 for r in semester_results if r.cgpa is not None and r.cgpa < 5.0)

    att_sessions = await AttendanceSession.find(
        Eq(AttendanceSession.tenant_id, tenant_id),
        Eq(AttendanceSession.status, AttendanceSessionStatus.SUBMITTED),
    ).to_list()
    if ay_label:
        att_sessions = [s for s in att_sessions if s.academic_year_label == ay_label]
    if sem_label:
        att_sessions = [s for s in att_sessions if s.semester_label == sem_label]
    session_ids = {s.id for s in att_sessions}
    att_by_user: dict[PydanticObjectId, list[int]] = defaultdict(lambda: [0, 0])
    if session_ids:
        att_records = await AttendanceRecord.find(
            Eq(AttendanceRecord.tenant_id, tenant_id),
            In(AttendanceRecord.session_id, list(session_ids)),
        ).to_list()
        for rec in att_records:
            if rec.student_user_id not in user_ids and user_ids:
                continue
            if rec.status in _ATTENDANCE_PRESENT:
                att_by_user[rec.student_user_id][0] += 1
            else:
                att_by_user[rec.student_user_id][1] += 1

    fails_by_user = {uid for uid in set(r.student_user_id for r in current_results if r.outcome == ExamSubjectResultOutcome.FAIL)}
    dual_risk = 0
    for uid in fails_by_user:
        present, absent = att_by_user.get(uid, [0, 0])
        total = present + absent
        if total == 0:
            continue
        if (present / total) * 100 < 75:
            dual_risk += 1

    academic_risk = [
        AcademicRiskItem(
            risk_key="arrears_3_plus",
            label="3 or more arrears",
            description="Students with three or more pending arrear courses",
            count=three_plus,
        ),
        AcademicRiskItem(
            risk_key="cgpa_below_5",
            label="CGPA below 5.0",
            description="Based on published semester results for the selected term",
            count=low_cgpa_count,
        ),
        AcademicRiskItem(
            risk_key="attendance_marks_low",
            label="Attendance and marks both low",
            description="Below 75% attendance with a failing subject mark",
            count=dual_risk,
        ),
    ]

    top_rows = sorted(
        [r for r in semester_results if r.cgpa is not None],
        key=lambda r: r.cgpa or 0,
        reverse=True,
    )[:3]
    top_user_ids = [r.student_user_id for r in top_rows]
    users = await User.find(In(User.id, top_user_ids)).to_list() if top_user_ids else []
    user_names = {u.id: u.full_name for u in users}
    top_performers: list[TopPerformerRow] = []
    for row in top_rows:
        profile = profile_by_user.get(row.student_user_id) or next(
            (p for p in profiles if p.user_id == row.student_user_id),
            None,
        )
        year_num = _study_year(profile.batch_label if profile else None, ay_label)
        prog = profile.programme_name or profile.programme_code if profile else row.programme_code
        study_label = f"Year {year_num}" if year_num else None
        programme_label = f"{prog} · {study_label}" if prog and study_label else prog
        top_performers.append(
            TopPerformerRow(
                user_id=str(row.student_user_id),
                full_name=user_names.get(row.student_user_id, "—"),
                programme_label=programme_label,
                study_year_label=study_label,
                cgpa=float(row.cgpa),
            )
        )

    results_display = None
    if sem_label and ay_label:
        year_start = ay_label.split("-")[0] if "-" in ay_label else ay_label
        results_display = f"{sem_label} semester {year_start} results"

    return AcademicPerformanceOverviewRead(
        filters=AcademicPerformanceFilters(
            academic_year_label=ay_label,
            semester_label=sem_label,
            programme_code=programme_code,
            study_year=study_year,
        ),
        academic_term=AcademicTermSummary(academic_year_label=ay_label, semester_label=sem_label),
        results_display_label=results_display,
        kpis=AcademicPerformanceKpiRead(
            overall_pass_rate_pct=overall_pass,
            overall_pass_rate_change_pts=change_pts,
            overall_pass_rate_reference_label=prev_label,
            average_cgpa=avg_cgpa,
            average_cgpa_ug=round(mean(ug_cgpas), 2) if ug_cgpas else None,
            average_cgpa_pg=round(mean(pg_cgpas), 2) if pg_cgpas else None,
            first_class_distinction_pct=distinction_pct,
            first_class_distinction_student_count=len(distinction_students),
            students_with_backlogs=len(backlog_users),
            students_with_backlogs_pct=backlog_pct,
            students_with_three_plus_arrears=three_plus,
        ),
        pass_rate_trend=trend_points,
        pass_rate_by_study_year=study_year_bars,
        low_pass_subjects=low_subjects[:12],
        grade_distribution=grade_distribution,
        academic_risk=academic_risk,
        top_performers=top_performers,
        generated_at=utcnow(),
    )