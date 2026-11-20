"""Department performance overview for college admin dashboard."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.modules.attendance.enums import AttendanceMarkStatus, AttendanceSessionStatus
from app.modules.attendance.models import AttendanceRecord, AttendanceSession
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.faculty_admin_models import FacultyEmploymentStatus, FacultyRecord
from app.modules.college_admin.identity_models import (
    DepartmentStaffAssociation,
    DepartmentStatus,
    InstitutionDepartment,
)
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AcademicTermSummary,
    DepartmentAttentionItem,
    DepartmentPassRateBarItem,
    DepartmentPerformanceFilters,
    DepartmentPerformanceKpiRead,
    DepartmentPerformanceOverviewRead,
    DepartmentScorecardRow,
)
from app.modules.examinations.exam_cell_grading_enums import ExamSubjectResultOutcome
from app.modules.examinations.exam_cell_grading_models import ExamStudentSubjectResult
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.faculty.models import FacultyProfile
from app.modules.hr.enums import HrJobOpeningStatus
from app.modules.hr.recruitment_models import HrJobOpening
from app.modules.students.models import StudentAcademicRecord, StudentProfile

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

_ATTENDANCE_PRESENT = frozenset(
    {AttendanceMarkStatus.PRESENT, AttendanceMarkStatus.LATE, AttendanceMarkStatus.EXCUSED}
)


def _programme_level(prog: AcademicProgramme) -> str:
    if prog.duration_semesters <= 4 and prog.credits_required <= 80:
        return "doctoral"
    if prog.duration_semesters <= 6:
        return "postgraduate"
    return "undergraduate"


def _level_matches(level: str, filter_level: str | None) -> bool:
    if not filter_level or filter_level in ("all", ""):
        return True
    norm = filter_level.lower()
    if norm in ("ug", "undergraduate"):
        return level == "undergraduate"
    if norm in ("pg", "postgraduate"):
        return level == "postgraduate"
    if norm in ("doctoral", "phd", "ph.d"):
        return level == "doctoral"
    return True


def _status_for_row(
    *,
    pass_rate: float | None,
    attendance: float | None,
    vacancies: int,
    college_pass_avg: float | None,
) -> tuple[str, str]:
    if pass_rate is not None and college_pass_avg is not None and pass_rate < college_pass_avg - 6:
        return "needs_review", "Needs review"
    if pass_rate is not None and pass_rate < 85:
        return "needs_review", "Needs review"
    if vacancies > 0 or (attendance is not None and attendance < 85):
        return "monitor", "Monitor"
    if pass_rate is not None and college_pass_avg is not None and pass_rate < college_pass_avg - 2:
        return "monitor", "Monitor"
    return "on_track", "On track"


async def get_department_performance_overview(
    scope: AccessScope,
    *,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    programme_code: str | None = None,
    programme_level: str | None = None,
    campus_id: str | None = None,
) -> DepartmentPerformanceOverviewRead:
    authorize(scope, Permission.COLLEGE_DASHBOARD_READ)
    tenant_id = require_college_tenant_scope(scope)
    campus_oid = to_object_id(campus_id, "campus_id") if campus_id else None

    year, semester = await _reader.current_academic_term(tenant_id)
    ay_label = academic_year_label or year
    sem_label = semester_label or semester

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    if campus_oid is not None:
        departments = [d for d in departments if campus_oid in d.campus_ids or not d.campus_ids]

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    prog_by_code = {p.programme_code.upper(): p for p in programmes if p.programme_code}

    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    students_by_dept: dict[str, list[StudentProfile]] = defaultdict(list)
    user_dept: dict[PydanticObjectId, PydanticObjectId | None] = {}

    for profile in profiles:
        if programme_code and (profile.programme_code or "").upper() != programme_code.upper():
            continue
        prog = prog_by_code.get((profile.programme_code or "").upper())
        if prog and not _level_matches(_programme_level(prog), programme_level):
            continue
        if profile.department_id is None:
            continue
        if campus_oid is not None and profile.department_id not in {d.id for d in departments}:
            continue
        students_by_dept[str(profile.department_id)].append(profile)
        user_dept[profile.user_id] = profile.department_id

    faculty_records = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    faculty_profiles = await FacultyProfile.find(Eq(FacultyProfile.tenant_id, tenant_id)).to_list()
    faculty_by_dept: dict[str, int] = defaultdict(int)
    seen_faculty: set[PydanticObjectId] = set()

    for rec in faculty_records:
        if rec.employment_status not in _ACTIVE_EMPLOYMENT:
            continue
        if rec.department_id is None:
            continue
        faculty_by_dept[str(rec.department_id)] += 1
        seen_faculty.add(rec.user_id)
    for fp in faculty_profiles:
        if fp.user_id in seen_faculty or fp.department_id is None:
            continue
        faculty_by_dept[str(fp.department_id)] += 1

    exam_sessions = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).to_list()
    if ay_label:
        exam_sessions = [s for s in exam_sessions if s.academic_year_label == ay_label]
    if sem_label:
        exam_sessions = [s for s in exam_sessions if s.semester_label == sem_label]
    session_ids = [s.id for s in exam_sessions]

    pass_stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    if session_ids:
        results = await ExamStudentSubjectResult.find(
            Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
            In(ExamStudentSubjectResult.exam_session_id, session_ids),
        ).to_list()
        for row in results:
            dept_id = user_dept.get(row.student_user_id)
            if dept_id is None:
                continue
            key = str(dept_id)
            if row.outcome == ExamSubjectResultOutcome.PASS:
                pass_stats[key][0] += 1
            elif row.outcome == ExamSubjectResultOutcome.FAIL:
                pass_stats[key][1] += 1

    attendance_sessions = await AttendanceSession.find(
        Eq(AttendanceSession.tenant_id, tenant_id),
        Eq(AttendanceSession.status, AttendanceSessionStatus.SUBMITTED),
    ).to_list()
    if ay_label:
        attendance_sessions = [s for s in attendance_sessions if s.academic_year_label == ay_label]
    if sem_label:
        attendance_sessions = [s for s in attendance_sessions if s.semester_label == sem_label]
    session_id_set = {s.id for s in attendance_sessions}
    att_counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    if session_id_set:
        records = await AttendanceRecord.find(
            Eq(AttendanceRecord.tenant_id, tenant_id),
            In(AttendanceRecord.session_id, list(session_id_set)),
        ).to_list()
        for rec in records:
            dept_id = user_dept.get(rec.student_user_id)
            if dept_id is None:
                continue
            key = str(dept_id)
            if rec.status in _ATTENDANCE_PRESENT:
                att_counts[key][0] += 1
            else:
                att_counts[key][1] += 1

    academic_rows = await StudentAcademicRecord.find(
        Eq(StudentAcademicRecord.tenant_id, tenant_id),
    ).to_list()
    if ay_label:
        academic_rows = [r for r in academic_rows if r.academic_year_label == ay_label]
    if sem_label:
        academic_rows = [r for r in academic_rows if r.semester_label == sem_label]
    cgpa_by_dept: dict[str, list[float]] = defaultdict(list)
    for row in academic_rows:
        if row.cgpa is None:
            continue
        dept_id = user_dept.get(row.user_id)
        if dept_id is None:
            continue
        cgpa_by_dept[str(dept_id)].append(float(row.cgpa))

    openings = await HrJobOpening.find(
        Eq(HrJobOpening.tenant_id, tenant_id),
        Eq(HrJobOpening.status, HrJobOpeningStatus.PUBLISHED),
    ).to_list()
    vacancies_by_dept: dict[str, int] = defaultdict(int)
    for opening in openings:
        open_slots = max(0, opening.vacancies - opening.filled_count)
        if open_slots <= 0:
            continue
        vacancies_by_dept[str(opening.department_id)] += open_slots

    acting_heads: set[str] = set()
    associations = await DepartmentStaffAssociation.find(
        Eq(DepartmentStaffAssociation.tenant_id, tenant_id),
    ).to_list()
    for assoc in associations:
        if "acting" in (assoc.association_role or "").lower():
            acting_heads.add(str(assoc.department_id))

    head_user_ids = [d.head_user_id for d in departments if d.head_user_id]
    head_users = await User.find(In(User.id, head_user_ids)).to_list() if head_user_ids else []
    head_names = {u.id: u.full_name for u in head_users}

    scorecard_rows: list[DepartmentScorecardRow] = []
    pass_rates_for_avg: list[float] = []

    for dept in departments:
        did = str(dept.id)
        passed, failed = pass_stats.get(did, [0, 0])
        total_results = passed + failed
        pass_rate = round((passed / total_results) * 100, 1) if total_results else None
        if pass_rate is not None:
            pass_rates_for_avg.append(pass_rate)

        present, absent = att_counts.get(did, [0, 0])
        att_total = present + absent
        attendance_pct = round((present / att_total) * 100, 1) if att_total else None

        cgpa_vals = cgpa_by_dept.get(did, [])
        avg_cgpa = round(mean(cgpa_vals), 2) if cgpa_vals else None

        vacancies = vacancies_by_dept.get(did, 0)
        status_key, status_label = _status_for_row(
            pass_rate=pass_rate,
            attendance=attendance_pct,
            vacancies=vacancies,
            college_pass_avg=None,
        )
        scorecard_rows.append(
            DepartmentScorecardRow(
                department_id=did,
                department_code=dept.department_code,
                department_name=dept.name,
                head_of_department=head_names.get(dept.head_user_id) if dept.head_user_id else None,
                head_acting=did in acting_heads,
                student_count=len(students_by_dept.get(did, [])),
                faculty_count=faculty_by_dept.get(did, 0),
                pass_rate_pct=pass_rate,
                attendance_pct=attendance_pct,
                average_cgpa=avg_cgpa,
                status_key=status_key,
                status_label=status_label,
            )
        )

    college_pass_avg = round(mean(pass_rates_for_avg), 1) if pass_rates_for_avg else None
    if college_pass_avg is not None:
        refreshed: list[DepartmentScorecardRow] = []
        for row in scorecard_rows:
            key, label = _status_for_row(
                pass_rate=row.pass_rate_pct,
                attendance=row.attendance_pct,
                vacancies=vacancies_by_dept.get(row.department_id, 0),
                college_pass_avg=college_pass_avg,
            )
            refreshed.append(row.model_copy(update={"status_key": key, "status_label": label}))
        scorecard_rows = refreshed

    scorecard_rows.sort(key=lambda r: r.department_name)

    best = max(
        (r for r in scorecard_rows if r.pass_rate_pct is not None),
        key=lambda r: r.pass_rate_pct or 0,
        default=None,
    )
    worst = min(
        (r for r in scorecard_rows if r.pass_rate_pct is not None),
        key=lambda r: r.pass_rate_pct or 100,
        default=None,
    )

    att_values = [r.attendance_pct for r in scorecard_rows if r.attendance_pct is not None]
    avg_att = round(mean(att_values), 1) if att_values else None
    above_85 = sum(1 for v in att_values if v >= 85)

    vacancy_total = sum(vacancies_by_dept.values())
    vacancy_depts = sum(1 for v in vacancies_by_dept.values() if v > 0)

    pass_bars = [
        DepartmentPassRateBarItem(
            department_id=r.department_id,
            department_code=r.department_code,
            department_name=r.department_name,
            pass_rate_pct=r.pass_rate_pct,
            status_key=r.status_key,
        )
        for r in scorecard_rows
        if r.pass_rate_pct is not None
    ]
    pass_bars.sort(key=lambda x: x.pass_rate_pct or 0, reverse=True)

    attention: list[DepartmentAttentionItem] = []
    if worst and college_pass_avg is not None and worst.pass_rate_pct is not None:
        gap = round(college_pass_avg - worst.pass_rate_pct, 1)
        if gap > 0:
            attention.append(
                DepartmentAttentionItem(
                    department_id=worst.department_id,
                    department_name=worst.department_name,
                    message=f"Pass rate {gap} pts below college average",
                    status_key="review",
                    status_label="Review",
                )
            )
    for dept_id, vac in sorted(vacancies_by_dept.items(), key=lambda x: -x[1])[:3]:
        if vac <= 0:
            continue
        dept = next((d for d in departments if str(d.id) == dept_id), None)
        if not dept:
            continue
        attention.append(
            DepartmentAttentionItem(
                department_id=dept_id,
                department_name=dept.name,
                message=f"{vac} faculty position{'s' if vac != 1 else ''} vacant",
                status_key="monitor",
                status_label="Monitor",
            )
        )
    for row in scorecard_rows:
        if row.head_acting:
            attention.append(
                DepartmentAttentionItem(
                    department_id=row.department_id,
                    department_name=row.department_name,
                    message="HoD position held in acting capacity",
                    status_key="action",
                    status_label="Action",
                )
            )
        elif not row.head_of_department:
            attention.append(
                DepartmentAttentionItem(
                    department_id=row.department_id,
                    department_name=row.department_name,
                    message="Head of department not assigned",
                    status_key="action",
                    status_label="Action",
                )
            )
    attention = attention[:6]

    semester_display = None
    if sem_label and ay_label:
        semester_display = f"{sem_label} semester {ay_label.split('-')[0] if '-' in ay_label else ay_label}"

    return DepartmentPerformanceOverviewRead(
        filters=DepartmentPerformanceFilters(
            academic_year_label=ay_label,
            semester_label=sem_label,
            programme_code=programme_code,
            programme_level=programme_level,
            campus_id=campus_id,
        ),
        academic_term=AcademicTermSummary(academic_year_label=ay_label, semester_label=sem_label),
        semester_display_label=semester_display,
        kpis=DepartmentPerformanceKpiRead(
            best_pass_rate_pct=best.pass_rate_pct if best else None,
            best_pass_rate_department_name=best.department_name if best else None,
            lowest_pass_rate_pct=worst.pass_rate_pct if worst else None,
            lowest_pass_rate_department_name=worst.department_name if worst else None,
            average_attendance_pct=avg_att,
            departments_above_attendance_threshold=above_85,
            departments_attendance_threshold_pct=85.0,
            departments_total_for_attendance=len(att_values),
            faculty_vacancies_total=vacancy_total,
            faculty_vacancies_department_count=vacancy_depts,
        ),
        scorecard=scorecard_rows,
        scorecard_total=len(scorecard_rows),
        scorecard_display_limit=8,
        pass_rate_by_department=pass_bars,
        needs_attention=attention,
        generated_at=utcnow(),
    )