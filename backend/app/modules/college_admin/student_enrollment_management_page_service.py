"""Student enrollment management list page (CA 06 — Enrollment tab)."""

from __future__ import annotations

import math
import re
from collections import defaultdict
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.attendance.models import AttendancePolicyReference, AttendanceRecord
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme, AcademicYear
from app.modules.college_admin.all_students_list_page_service import (
    _attendance_pct,
    _fee_presentation,
    _programme_label,
    _register_number,
)
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    PoliciesPagination,
    StudentAdminDashboardFilterOption,
    StudentEnrollmentBulkEnrollPayload,
    StudentEnrollmentManagementPageRead,
    StudentEnrollmentManagementTableRow,
    UserDashboardKpi,
)
from app.modules.college_admin.student_admin_models import StudentLifecycleStatus, StudentRecord
from app.modules.college_admin.student_administration_dashboard_page_service import _fmt_time_label
from app.modules.college_admin.student_statistics_overview_service import _study_year
from app.modules.finance.finance_models import StudentFeeDemand
from app.modules.students.enums import AcademicStanding, ProgressionStatus, StudentEnrollmentStatus
from app.modules.students.models import StudentAcademicRecord, StudentProfile

_reader = OperationalDataReader()
_PAGE_SIZE = 10

_ELIGIBLE_LIFECYCLE = frozenset(
    {
        StudentLifecycleStatus.ACTIVE,
        StudentLifecycleStatus.ADMITTED,
    }
)

def _ay_display(code: str) -> str:
    return code.replace("-", "–") if code else "—"


def _term_key(academic_year: str, semester_label: str) -> str:
    return f"{academic_year}::{semester_label}"


def _parse_term_key(term_key: str | None, default_ay: str, default_sem: str) -> tuple[str, str]:
    if term_key and "::" in term_key:
        ay, sem = term_key.split("::", 1)
        if ay and sem:
            return ay, sem
    return default_ay, default_sem


def _term_option_label(academic_year: str, semester_label: str) -> str:
    sem = (semester_label or "").strip()
    ay = _ay_display(academic_year)
    if not sem:
        return f"AY {ay}"
    return f"{sem.replace('-', '–')} {ay}"


def _semester_display(semester_label: str | None, study_year: int | None) -> str:
    if semester_label:
        match = re.search(r"\d+", semester_label)
        if match:
            return match.group(0)
    if study_year is not None:
        return str(study_year)
    return "—"


def _fee_column(fee_raw: str, fee_tone: str) -> tuple[str, str]:
    if fee_raw == "Paid":
        return "Cleared", "success"
    if fee_raw in ("Overdue", "Partial"):
        return "Dues", "error"
    return "Cleared", "success" if fee_tone == "success" else "muted"


def _enrollment_column(
    *,
    record: StudentRecord,
    user: User,
    term_record: StudentAcademicRecord | None,
    fee_cleared: bool,
    attendance_pct: float | None,
    min_attendance: float,
    standing: AcademicStanding | None,
) -> tuple[str, str, str]:
    if record.lifecycle_status == StudentLifecycleStatus.ON_LEAVE:
        return "on_hold", "On hold", "warning"
    if not user.is_active or standing == AcademicStanding.SUSPENDED:
        return "on_hold", "On hold", "warning"
    if standing in (AcademicStanding.PROBATION, AcademicStanding.SUSPENDED):
        return "on_hold", "On hold", "warning"
    if attendance_pct is not None and attendance_pct < min_attendance:
        return "on_hold", "On hold", "warning"
    if not fee_cleared:
        return "on_hold", "On hold", "warning"

    if term_record and term_record.enrollment_status in (
        StudentEnrollmentStatus.ACTIVE,
        StudentEnrollmentStatus.COMPLETED,
    ):
        return "enrolled", "Enrolled", "success"
    if record.enrollment_status == StudentEnrollmentStatus.PROVISIONAL or (
        term_record and term_record.enrollment_status == StudentEnrollmentStatus.PROVISIONAL
    ):
        return "pending", "Pending", "info"
    if term_record is None:
        return "pending", "Pending", "info"
    return "pending", "Pending", "info"


async def get_student_enrollment_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    term_key: str | None = None,
    programme_code: str | None = None,
) -> StudentEnrollmentManagementPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    default_ay, default_sem = await _reader.current_academic_term(tenant_id)
    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-year_code").to_list()
    if not default_ay and years:
        default_ay = years[0].year_code
    if not default_sem:
        default_sem = "Odd"

    selected_ay, selected_sem = _parse_term_key(term_key, default_ay or "", default_sem or "Odd")

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    programme_by_code = {p.programme_code.upper(): p for p in programmes}

    policy = await AttendancePolicyReference.find_one(
        Eq(AttendancePolicyReference.tenant_id, tenant_id),
        Eq(AttendancePolicyReference.is_active, True),
    )
    min_attendance = policy.rules.min_percentage_required if policy else 75.0

    records = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).sort("-created_at").to_list()
    if not records:
        empty_pagination = PoliciesPagination(
            page=1,
            page_size=_PAGE_SIZE,
            total=0,
            total_pages=0,
            page_numbers=[],
            has_previous=False,
            has_next=False,
        )
        return StudentEnrollmentManagementPageRead(
            page_title="Student Enrollment Management",
            page_subtitle=f"Semester enrollment for AY {_ay_display(selected_ay)}" if selected_ay else "Semester enrollment",
            export_label="Export",
            enroll_selected_label="Enroll selected",
            term_filter_label="Term",
            programme_filter_label="Programme",
            scope_indicator_label="College scope",
            updated_at_label=_fmt_time_label(now),
            term_options=[],
            programme_options=[StudentAdminDashboardFilterOption(value="", label="All programmes")],
            selected_term_key=_term_key(selected_ay, selected_sem),
            selected_programme_code=programme_code or "",
            kpis=[
                UserDashboardKpi(key="eligible", label="Eligible", value="0", hint_line="Active students", hint_tone="info"),
                UserDashboardKpi(key="enrolled", label="Enrolled", value="0", hint_line="—", hint_tone="success"),
                UserDashboardKpi(key="pending", label="Pending", value="0", hint_line="Fee or eligibility", hint_tone="warning"),
                UserDashboardKpi(key="on_hold", label="On hold", value="0", hint_line="Dues or attendance", hint_tone="error"),
            ],
            enrollment_section_title="Enrollment",
            enrollment_count_label="0 students",
            table_headers=["Student", "Register no.", "Programme", "Sem", "Fee", "Enrollment"],
            enrollment_rows=[],
            showing_label="Showing 0 of 0",
            pagination=empty_pagination,
            footer_disclaimer="Live institutional data · Student enrollment and fee records · All times IST",
            footer_snapshot_label="Snapshot",
            generated_at=now,
        )

    user_ids = list({r.user_id for r in records})
    users = await User.find(In(User.id, user_ids)).to_list()
    user_by_id = {u.id: u for u in users if u.id is not None}

    profiles = await StudentProfile.find(
        Eq(StudentProfile.tenant_id, tenant_id),
        In(StudentProfile.user_id, user_ids),
    ).to_list()
    profile_by_user = {p.user_id: p for p in profiles}

    fee_demands = await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, tenant_id)).to_list()
    demands_by_user: dict[PydanticObjectId, list[StudentFeeDemand]] = defaultdict(list)
    for demand in fee_demands:
        demands_by_user[demand.student_user_id].append(demand)

    attendance_rows = await AttendanceRecord.find(Eq(AttendanceRecord.tenant_id, tenant_id)).to_list()
    attendance_by_user: dict[PydanticObjectId, list[AttendanceRecord]] = defaultdict(list)
    for row in attendance_rows:
        attendance_by_user[row.student_user_id].append(row)

    academic_records = await StudentAcademicRecord.find(Eq(StudentAcademicRecord.tenant_id, tenant_id)).to_list()
    term_record_by_user: dict[PydanticObjectId, StudentAcademicRecord] = {}
    standing_by_user: dict[PydanticObjectId, AcademicStanding] = {}
    term_pairs: set[tuple[str, str]] = set()

    for ar in academic_records:
        term_pairs.add((ar.academic_year_label, ar.semester_label))
        if ar.academic_year_label == selected_ay and ar.semester_label == selected_sem:
            term_record_by_user[ar.user_id] = ar
        prev = standing_by_user.get(ar.user_id)
        if ar.academic_year_label == selected_ay and ar.semester_label == selected_sem:
            standing_by_user[ar.user_id] = ar.academic_standing
        elif prev is None:
            standing_by_user[ar.user_id] = ar.academic_standing

    if default_ay and default_sem:
        term_pairs.add((default_ay, default_sem))
    if selected_ay and selected_sem:
        term_pairs.add((selected_ay, selected_sem))

    term_options = [StudentAdminDashboardFilterOption(value="", label="Term")]
    for ay, sem in sorted(term_pairs, key=lambda pair: (pair[0], pair[1]), reverse=True):
        term_options.append(
            StudentAdminDashboardFilterOption(
                value=_term_key(ay, sem),
                label=_term_option_label(ay, sem),
            )
        )
    if len(term_options) == 1 and selected_ay:
        term_options.append(
            StudentAdminDashboardFilterOption(
                value=_term_key(selected_ay, selected_sem),
                label=_term_option_label(selected_ay, selected_sem),
            )
        )

    programme_codes: set[str] = set()
    for record in records:
        if record.programme_code:
            programme_codes.add(record.programme_code.upper())

    programme_options = [StudentAdminDashboardFilterOption(value="", label="All programmes")]
    for code in sorted(programme_codes):
        prog = programme_by_code.get(code)
        programme_options.append(
            StudentAdminDashboardFilterOption(value=code, label=prog.name if prog else code),
        )

    programme_q = programme_code.upper() if programme_code else None

    eligible_rows: list[tuple] = []
    counts = {"eligible": 0, "enrolled": 0, "pending": 0, "on_hold": 0}

    for record in records:
        if record.lifecycle_status not in _ELIGIBLE_LIFECYCLE:
            continue
        user = user_by_id.get(record.user_id)
        if user is None:
            continue
        if programme_q and (record.programme_code or "").upper() != programme_q:
            continue

        profile = profile_by_user.get(record.user_id)
        register_no = _register_number(record, profile)
        programme_label = _programme_label(record.programme_code, profile, programme_by_code)
        study_year = _study_year(record.batch_label or (profile.batch_label if profile else None), selected_ay)
        sem_label = _semester_display(selected_sem, study_year)

        fee_raw, fee_tone = _fee_presentation(demands_by_user.get(record.user_id, []))
        fee_label, fee_col_tone = _fee_column(fee_raw, fee_tone)
        fee_cleared = fee_label == "Cleared"

        att_pct = _attendance_pct(attendance_by_user.get(record.user_id, []))
        standing = standing_by_user.get(record.user_id)
        term_record = term_record_by_user.get(record.user_id)

        enroll_code, enroll_label, enroll_tone = _enrollment_column(
            record=record,
            user=user,
            term_record=term_record,
            fee_cleared=fee_cleared,
            attendance_pct=att_pct,
            min_attendance=min_attendance,
            standing=standing,
        )

        counts["eligible"] += 1
        counts[enroll_code] += 1

        detail_href = f"/college-admin/students/student-details?id={record.id}"
        is_selectable = enroll_code == "pending" and fee_cleared

        eligible_rows.append(
            (
                record,
                user.full_name,
                register_no,
                programme_label,
                sem_label,
                fee_label,
                fee_col_tone,
                enroll_label,
                enroll_tone,
                enroll_code,
                detail_href,
                is_selectable,
            )
        )

    enrolled_pct = round((counts["enrolled"] / counts["eligible"]) * 100, 1) if counts["eligible"] else 0.0

    kpis = [
        UserDashboardKpi(
            key="eligible",
            label="Eligible",
            value=f"{counts['eligible']:,}",
            hint_line="Active students",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="enrolled",
            label="Enrolled",
            value=f"{counts['enrolled']:,}",
            hint_line=f"{enrolled_pct:g}%" if counts["eligible"] else "—",
            hint_tone="success",
        ),
        UserDashboardKpi(
            key="pending",
            label="Pending",
            value=f"{counts['pending']:,}",
            hint_line="Fee or eligibility",
            hint_tone="warning",
        ),
        UserDashboardKpi(
            key="on_hold",
            label="On hold",
            value=f"{counts['on_hold']:,}",
            hint_line="Dues or attendance",
            hint_tone="error",
        ),
    ]

    total = len(eligible_rows)
    total_pages = math.ceil(total / _PAGE_SIZE) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_slice = eligible_rows[start : start + _PAGE_SIZE]

    table_rows: list[StudentEnrollmentManagementTableRow] = []
    for (
        record,
        student_name,
        register_no,
        programme_label,
        sem_label,
        fee_label,
        fee_col_tone,
        enroll_label,
        enroll_tone,
        _enroll_code,
        detail_href,
        is_selectable,
    ) in page_slice:
        table_rows.append(
            StudentEnrollmentManagementTableRow(
                record_id=str(record.id),
                student_name=student_name,
                register_number=register_no,
                programme_label=programme_label,
                semester_label=sem_label,
                fee_status_label=fee_label,
                fee_status_tone=fee_col_tone,
                enrollment_status_label=enroll_label,
                enrollment_status_tone=enroll_tone,
                detail_href=detail_href,
                is_selectable=is_selectable,
            )
        )

    page_numbers = list(range(1, min(total_pages, 12) + 1)) if total_pages else []
    if total_pages > 12:
        page_numbers = [1, 2, 3, -1, total_pages]

    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)

    subtitle = (
        f"Semester enrollment for AY {_ay_display(selected_ay)}"
        if selected_ay
        else "Semester enrollment for the college"
    )

    return StudentEnrollmentManagementPageRead(
        page_title="Student Enrollment Management",
        page_subtitle=subtitle,
        export_label="Export",
        enroll_selected_label="Enroll selected",
        term_filter_label="Term",
        programme_filter_label="Programme",
        scope_indicator_label="College scope",
        updated_at_label=_fmt_time_label(now),
        term_options=term_options,
        programme_options=programme_options,
        selected_term_key=_term_key(selected_ay, selected_sem),
        selected_programme_code=programme_code or "",
        kpis=kpis,
        enrollment_section_title="Enrollment",
        enrollment_count_label=f"{counts['eligible']:,} students",
        table_headers=["Student", "Register no.", "Programme", "Sem", "Fee", "Enrollment"],
        enrollment_rows=table_rows,
        showing_label=f"Showing {showing_from}–{showing_to} of {total:,}" if total else f"Showing 0 of {counts['eligible']:,}",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=page_numbers,
            has_previous=page > 1 and bool(total),
            has_next=page < total_pages,
        ),
        footer_disclaimer="Live institutional data · Student enrollment and fee records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def bulk_enroll_students_for_term(
    scope: AccessScope,
    payload: StudentEnrollmentBulkEnrollPayload,
) -> StudentEnrollmentManagementPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)

    if not payload.record_ids:
        raise AppError(code="VALIDATION", message="Select at least one student", status_code=422)

    default_ay, default_sem = await _reader.current_academic_term(tenant_id)
    selected_ay, selected_sem = _parse_term_key(
        payload.term_key,
        default_ay or "",
        default_sem or "Odd",
    )

    now = utcnow()
    for raw_id in payload.record_ids:
        record_id = to_object_id(raw_id, "record_id")
        record = await StudentRecord.get(record_id)
        if record is None or record.tenant_id != tenant_id:
            continue
        if record.lifecycle_status not in _ELIGIBLE_LIFECYCLE:
            continue

        existing = await StudentAcademicRecord.find_one(
            Eq(StudentAcademicRecord.tenant_id, tenant_id),
            Eq(StudentAcademicRecord.user_id, record.user_id),
            Eq(StudentAcademicRecord.academic_year_label, selected_ay),
            Eq(StudentAcademicRecord.semester_label, selected_sem),
        )
        if existing:
            existing.enrollment_status = StudentEnrollmentStatus.ACTIVE
            existing.progression_status = ProgressionStatus.PROMOTED
            existing.updated_at = now
            await existing.save()
        else:
            doc = StudentAcademicRecord(
                tenant_id=tenant_id,
                user_id=record.user_id,
                academic_year_label=selected_ay,
                semester_label=selected_sem,
                enrollment_status=StudentEnrollmentStatus.ACTIVE,
                progression_status=ProgressionStatus.PROMOTED,
                effective_from=now.date(),
            )
            await doc.insert()

        record.enrollment_status = StudentEnrollmentStatus.ACTIVE
        record.updated_at = now
        record.updated_by = scope.user_id
        await record.save()

    return await get_student_enrollment_management_page(
        scope,
        page=payload.page,
        term_key=_term_key(selected_ay, selected_sem),
        programme_code=payload.programme_code or None,
    )