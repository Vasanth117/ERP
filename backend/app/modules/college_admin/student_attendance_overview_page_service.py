"""Student attendance overview (CA 08.02)."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import mean
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.attendance.enums import AttendanceMarkStatus, AttendanceSessionStatus
from app.modules.attendance.models import AttendanceRecord, AttendanceSession
from app.modules.attendance.policy_engine import calculate_percentage
from app.modules.college_admin.academic_config_models import AcademicProgramme, AcademicYear
from app.modules.college_admin.attendance_dashboard_page_service import (
    _parse_term_key,
    _term_key,
    _term_label,
)
from app.modules.college_admin.attendance_overview_service import (
    _PRESENT_MARKS,
    _policy_thresholds,
    _student_policy_rules,
)
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.models import InstitutionSettings
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    StudentAdminDashboardFilterOption,
    StudentAttendanceDistributionBar,
    StudentAttendanceOverviewPageRead,
    StudentAttendanceProgrammeRow,
    UserDashboardKpi,
)
from app.modules.college_admin.student_admin_models import StudentLifecycleStatus, StudentRecord
from app.modules.students.models import StudentProfile

_IST = ZoneInfo("Asia/Kolkata")
_reader = OperationalDataReader()
_ABOVE_PCT = 90.0
_ENROLLED = frozenset(
    {
        StudentLifecycleStatus.ADMITTED.value,
        StudentLifecycleStatus.ACTIVE.value,
        StudentLifecycleStatus.ON_LEAVE.value,
    }
)


def _fmt_time_label(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Updated %H:%M IST")


def _fmt_snapshot(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Snapshot · %d %b %Y, %H:%M IST")


def _programme_label(code: str, programmes: dict[str, AcademicProgramme]) -> str:
    prog = programmes.get(code.upper())
    if prog and prog.name:
        return prog.name
    if prog and prog.code:
        return prog.code
    return code.upper() if code else "—"


async def get_student_attendance_overview_page(
    scope: AccessScope,
    *,
    term_key: str | None = None,
    programme_code: str | None = None,
) -> StudentAttendanceOverviewPageRead:
    authorize(scope, Permission.ATTENDANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    ay_override, sem_override = _parse_term_key(term_key)
    current_ay, current_sem = await _reader.current_academic_term(tenant_id)
    ay_label = ay_override or current_ay
    sem_label = sem_override or current_sem
    prog_filter = programme_code.upper().strip() if programme_code else None

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

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    programme_by_code = {(p.code or "").upper(): p for p in programmes if p.code}
    programme_options = [StudentAdminDashboardFilterOption(value="", label="All programmes")]
    for prog in sorted(programmes, key=lambda p: p.name or p.code or ""):
        if not prog.code:
            continue
        programme_options.append(
            StudentAdminDashboardFilterOption(value=prog.code.upper(), label=prog.name or prog.code),
        )

    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    profile_by_user = {p.user_id: p for p in profiles}
    records = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).to_list()

    enrolled: list[tuple[PydanticObjectId, str | None]] = []
    seen: set[PydanticObjectId] = set()

    def matches_prog(code: str | None) -> bool:
        if not prog_filter:
            return True
        return (code or "").upper() == prog_filter

    for record in records:
        if record.lifecycle_status.value not in _ENROLLED:
            continue
        code = record.programme_code or (profile_by_user.get(record.user_id).programme_code if profile_by_user.get(record.user_id) else None)
        if not matches_prog(code):
            continue
        seen.add(record.user_id)
        enrolled.append((record.user_id, (code or "").upper() or None))

    for profile in profiles:
        if profile.user_id in seen:
            continue
        code = profile.programme_code
        if not matches_prog(code):
            continue
        enrolled.append((profile.user_id, (code or "").upper() or None))

    sessions = await AttendanceSession.find(
        Eq(AttendanceSession.tenant_id, tenant_id),
        Eq(AttendanceSession.status, AttendanceSessionStatus.SUBMITTED),
    ).to_list()
    if ay_label:
        sessions = [s for s in sessions if s.academic_year_label == ay_label]
    if sem_label:
        sessions = [s for s in sessions if s.semester_label == sem_label]
    session_ids = {s.id for s in sessions}

    student_pct: dict[PydanticObjectId, float] = {}
    enrolled_ids = {uid for uid, _ in enrolled}
    if session_ids:
        att_records = await AttendanceRecord.find(
            Eq(AttendanceRecord.tenant_id, tenant_id),
            In(AttendanceRecord.session_id, list(session_ids)),
        ).to_list()
        by_student: dict[PydanticObjectId, list[AttendanceRecord]] = defaultdict(list)
        for rec in att_records:
            if rec.student_user_id in enrolled_ids:
                by_student[rec.student_user_id].append(rec)
        for uid, recs in by_student.items():
            if rules and recs:
                student_pct[uid] = calculate_percentage(recs, rules)
            elif recs:
                present = sum(1 for r in recs if r.status in _PRESENT_MARKS)
                student_pct[uid] = round((present / len(recs)) * 100, 2)

    pct_values = [student_pct[uid] for uid in enrolled_ids if uid in student_pct]
    overall_avg = round(mean(pct_values), 1) if pct_values else None

    above_90 = sum(1 for v in pct_values if v >= _ABOVE_PCT)
    band_mid = sum(1 for v in pct_values if minimum_pct <= v < _ABOVE_PCT)
    below_min = sum(1 for v in pct_values if v < minimum_pct)
    total_with_pct = len(pct_values)

    def share(count: int) -> float:
        return round((count / total_with_pct) * 100) if total_with_pct else 0.0

    hint_for_average = "All programmes"
    if prog_filter:
        hint_for_average = _programme_label(prog_filter, programme_by_code)

    kpis = [
        UserDashboardKpi(
            key="average",
            label="Average",
            value=f"{overall_avg:g}%" if overall_avg is not None else "—",
            hint_line=hint_for_average,
            hint_tone="success",
        ),
        UserDashboardKpi(
            key="above_90",
            label="Above 90%",
            value=str(above_90),
            hint_line=f"{share(above_90):g}%",
            hint_tone="success",
        ),
        UserDashboardKpi(
            key="band_75_90",
            label=f"{minimum_pct:g}–90%",
            value=str(band_mid),
            hint_line=f"{share(band_mid):g}%",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="below_minimum",
            label=f"Below {minimum_pct:g}%",
            value=str(below_min),
            hint_line=f"{share(below_min):g}%",
            hint_tone="error",
        ),
    ]

    programme_students: dict[str, list[PydanticObjectId]] = defaultdict(list)
    for uid, code in enrolled:
        key = code or "_unassigned"
        programme_students[key].append(uid)

    programme_rows: list[StudentAttendanceProgrammeRow] = []
    for code, students in programme_students.items():
        if code == "_unassigned":
            continue
        prog_pcts = [student_pct[uid] for uid in students if uid in student_pct]
        prog_avg = round(mean(prog_pcts), 0) if prog_pcts else None
        prog_below = sum(1 for uid in students if uid in student_pct and student_pct[uid] < minimum_pct)
        programme_rows.append(
            StudentAttendanceProgrammeRow(
                programme_code=code,
                programme_label=_programme_label(code, programme_by_code),
                student_count=len(students),
                average_pct=prog_avg,
                below_minimum_count=prog_below,
            ),
        )
    programme_rows.sort(key=lambda r: (-r.student_count, r.programme_label))

    distribution_bars = [
        StudentAttendanceDistributionBar(
            bucket_key="above_90",
            label="Above 90%",
            student_count=above_90,
            share_pct=share(above_90),
            bar_tone="success",
        ),
        StudentAttendanceDistributionBar(
            bucket_key="band_mid",
            label=f"{minimum_pct:g}–90%",
            student_count=band_mid,
            share_pct=share(band_mid),
            bar_tone="info",
        ),
        StudentAttendanceDistributionBar(
            bucket_key="below_minimum",
            label=f"Below {minimum_pct:g}%",
            student_count=below_min,
            share_pct=share(below_min),
            bar_tone="error",
        ),
    ]

    return StudentAttendanceOverviewPageRead(
        page_title="Student Attendance Overview",
        page_subtitle="Across programmes and semesters",
        export_label="Export",
        term_filter_label="Academic term",
        programme_filter_label="Programme",
        scope_indicator_label="College scope",
        updated_at_label=_fmt_time_label(now),
        term_options=term_options,
        programme_options=programme_options,
        selected_term_key=_term_key(ay_label, sem_label),
        selected_programme_code=prog_filter or "",
        kpis=kpis,
        programme_table_title="By programme",
        programme_table_headers=["Programme", "Students", "Average", f"Below {minimum_pct:g}%"],
        programme_rows=programme_rows,
        programme_table_footer_label=f"{len(programme_rows)} programmes",
        distribution_title="Distribution",
        distribution_bars=distribution_bars,
        footer_disclaimer="Live institutional data · Student attendance · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )