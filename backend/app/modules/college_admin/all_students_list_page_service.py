"""All students list page (CA 06.02)."""

from __future__ import annotations

import math
from collections import defaultdict
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.attendance.enums import AttendanceMarkStatus
from app.modules.attendance.models import AttendancePolicyReference, AttendanceRecord
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AllStudentsListPageRead,
    AllStudentsListTableRow,
    PoliciesPagination,
    UserListFilterOption,
)
from app.modules.college_admin.student_admin_models import StudentLifecycleStatus, StudentRecord
from app.modules.college_admin.student_statistics_overview_service import _programme_group_key, _study_year
from app.modules.finance.finance_enums import FeeDemandStatus
from app.modules.finance.finance_models import StudentFeeDemand
from app.modules.students.enums import AcademicStanding
from app.modules.students.models import StudentAcademicRecord, StudentProfile

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 10
_reader = OperationalDataReader()

_PRESENT_MARKS = frozenset(
    {
        AttendanceMarkStatus.PRESENT,
        AttendanceMarkStatus.LATE,
        AttendanceMarkStatus.EXCUSED,
    }
)

_STATUS_FILTERS: list[tuple[str, str]] = [
    ("", "Status"),
    ("active", "Active"),
    ("provisional", "Provisional"),
    ("on_leave", "On leave"),
    ("shortage", "Shortage"),
    ("suspended", "Suspended"),
    ("discontinued", "Discontinued"),
]


def _programme_label(code: str | None, profile: StudentProfile | None, programmes: dict[str, AcademicProgramme]) -> str:
    if profile and profile.programme_name:
        return profile.programme_name
    if code and code in programmes:
        return programmes[code].name
    return code or "—"


def _register_number(record: StudentRecord, profile: StudentProfile | None) -> str:
    for candidate in (record.roll_number, record.student_id, profile.roll_number if profile else None):
        if candidate:
            return candidate
    return "—"


def _year_section_label(record: StudentRecord, ay_label: str | None) -> str:
    year = _study_year(record.batch_label, ay_label)
    section = (record.section_code or "").strip() or "—"
    year_part = str(year) if year is not None else "—"
    return f"{year_part} / {section}"


def _fee_presentation(demands: list[StudentFeeDemand]) -> tuple[str, str]:
    open_demands = [d for d in demands if d.status != FeeDemandStatus.WAIVED]
    if not open_demands:
        return "—", "muted"
    statuses = {d.status for d in open_demands}
    if FeeDemandStatus.OVERDUE in statuses:
        return "Overdue", "error"
    if FeeDemandStatus.OPEN in statuses or FeeDemandStatus.PARTIALLY_PAID in statuses:
        return "Partial", "warning"
    if all(d.status == FeeDemandStatus.PAID for d in open_demands):
        return "Paid", "success"
    return "Partial", "warning"


def _attendance_pct(records: list[AttendanceRecord]) -> float | None:
    if not records:
        return None
    present = sum(1 for row in records if row.status in _PRESENT_MARKS)
    return round((present / len(records)) * 100, 1)


def _student_status_code(
    record: StudentRecord,
    user: User,
    *,
    attendance_pct: float | None,
    min_attendance: float,
    standing: AcademicStanding | None,
) -> tuple[str, str, str]:
    if record.lifecycle_status == StudentLifecycleStatus.ON_LEAVE:
        return "on_leave", "On leave", "info"
    if not user.is_active:
        return "suspended", "Suspended", "error"
    if record.lifecycle_status == StudentLifecycleStatus.ADMITTED:
        return "provisional", "Provisional", "info"
    if record.lifecycle_status in (StudentLifecycleStatus.WITHDRAWN, StudentLifecycleStatus.DISCONTINUED):
        return "discontinued", "Discontinued", "muted"
    if standing in (AcademicStanding.PROBATION, AcademicStanding.SUSPENDED):
        return "shortage", "Shortage", "warning"
    if attendance_pct is not None and attendance_pct < min_attendance:
        return "shortage", "Shortage", "warning"
    if record.lifecycle_status == StudentLifecycleStatus.ACTIVE:
        return "active", "Active", "success"
    label = record.lifecycle_status.value.replace("_", " ").title()
    return record.lifecycle_status.value, label, "muted"


def _matches_search(
    *,
    query: str,
    user: User,
    record: StudentRecord,
    profile: StudentProfile | None,
    register_no: str,
) -> bool:
    if not query:
        return True
    q = query.lower()
    blobs = [
        user.full_name,
        user.email,
        register_no,
        record.contact_phone or "",
        profile.contact_phone if profile else "",
        profile.alternate_email if profile else "",
    ]
    return any(q in (value or "").lower() for value in blobs)


async def get_all_students_list_page(
    scope: AccessScope,
    *,
    page: int = 1,
    search: str | None = None,
    programme_code: str | None = None,
    study_year: int | None = None,
    section_code: str | None = None,
    status_filter: str | None = None,
) -> AllStudentsListPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    ay_label, _ = await _reader.current_academic_term(tenant_id)

    policy = await AttendancePolicyReference.find_one(
        Eq(AttendancePolicyReference.tenant_id, tenant_id),
        Eq(AttendancePolicyReference.is_active, True),
    )
    min_attendance = policy.rules.min_percentage_required if policy else 75.0

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    programme_by_code = {p.programme_code.upper(): p for p in programmes}

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
        return AllStudentsListPageRead(
            page_title="All Students List",
            page_subtitle="Search and manage every student record in the college",
            export_label="Export",
            add_student_label="Add student",
            add_student_href="/college-admin/students/new-student-registration",
            bulk_actions_label="Bulk actions",
            bulk_actions_href="/college-admin/students/bulk-student-import",
            search_placeholder="Search name, register number, phone or email...",
            programme_filter_label="Programme",
            year_filter_label="Year",
            section_filter_label="Section",
            status_filter_label="Status",
            programme_options=[UserListFilterOption(value="", label="Programme")],
            year_options=[UserListFilterOption(value="", label="Year")],
            section_options=[UserListFilterOption(value="", label="Section")],
            status_options=[UserListFilterOption(value=v, label=lbl) for v, lbl in _STATUS_FILTERS],
            students_section_title="Students",
            students_count_label="0 students",
            table_headers=["Student", "Register no.", "Programme", "Year / Sec", "Attendance", "Fee status", "Status"],
            students=[],
            showing_label="Showing 0 of 0",
            pagination=empty_pagination,
            footer_disclaimer="Live institutional data · Student, attendance and finance records · All times IST",
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

    attendance_rows = await AttendanceRecord.find(Eq(AttendanceRecord.tenant_id, tenant_id)).to_list()
    attendance_by_user: dict[PydanticObjectId, list[AttendanceRecord]] = defaultdict(list)
    for row in attendance_rows:
        attendance_by_user[row.student_user_id].append(row)

    fee_demands = await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, tenant_id)).to_list()
    demands_by_user: dict[PydanticObjectId, list[StudentFeeDemand]] = defaultdict(list)
    for demand in fee_demands:
        demands_by_user[demand.student_user_id].append(demand)

    academic_records = await StudentAcademicRecord.find(Eq(StudentAcademicRecord.tenant_id, tenant_id)).to_list()
    standing_by_user: dict[PydanticObjectId, AcademicStanding] = {}
    standing_updated: dict[PydanticObjectId, datetime] = {}
    for ar in academic_records:
        prev_at = standing_updated.get(ar.user_id)
        if prev_at is None or ar.updated_at >= prev_at:
            standing_updated[ar.user_id] = ar.updated_at
            standing_by_user[ar.user_id] = ar.academic_standing

    search_q = (search or "").strip()
    programme_q = programme_code.upper() if programme_code else None
    section_q = section_code.strip().upper() if section_code else None

    rows: list[tuple] = []
    for record in records:
        user = user_by_id.get(record.user_id)
        if user is None:
            continue
        profile = profile_by_user.get(record.user_id)
        register_no = _register_number(record, profile)

        if programme_q and (record.programme_code or "").upper() != programme_q:
            continue
        if section_q and (record.section_code or "").upper() != section_q:
            continue
        if study_year is not None:
            computed = _study_year(record.batch_label, ay_label)
            prog_key = _programme_group_key(record.programme_code, profile.programme_name if profile else None)
            if study_year >= 5:
                if not (computed is not None and computed >= 5) and prog_key != "phd":
                    continue
            elif computed != study_year:
                continue

        attendance_pct = _attendance_pct(attendance_by_user.get(record.user_id, []))
        status_code, status_label, status_tone = _student_status_code(
            record,
            user,
            attendance_pct=attendance_pct,
            min_attendance=min_attendance,
            standing=standing_by_user.get(record.user_id),
        )
        if status_filter and status_code != status_filter:
            continue
        if not _matches_search(
            query=search_q,
            user=user,
            record=record,
            profile=profile,
            register_no=register_no,
        ):
            continue

        programme_label = _programme_label(record.programme_code, profile, programme_by_code)
        year_section = _year_section_label(record, ay_label)
        fee_label, fee_tone = _fee_presentation(demands_by_user.get(record.user_id, []))

        if attendance_pct is None:
            attendance_label = "—"
            attendance_tone = "muted"
        else:
            attendance_label = f"{attendance_pct:.1f}%"
            attendance_tone = "success" if attendance_pct >= min_attendance else "warning"

        rows.append((record, user, profile, register_no, programme_label, year_section, attendance_label, attendance_tone, fee_label, fee_tone, status_label, status_tone))

    total = len(rows)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_slice = rows[start : start + _PAGE_SIZE]

    table_rows: list[AllStudentsListTableRow] = []
    for (
        record,
        user,
        _profile,
        register_no,
        programme_label,
        year_section,
        attendance_label,
        attendance_tone,
        fee_label,
        fee_tone,
        status_label,
        status_tone,
    ) in page_slice:
        table_rows.append(
            AllStudentsListTableRow(
                record_id=str(record.id),
                student_name=user.full_name,
                register_number=register_no,
                programme_label=programme_label,
                year_section_label=year_section,
                attendance_label=attendance_label,
                attendance_tone=attendance_tone,
                fee_status_label=fee_label,
                fee_status_tone=fee_tone,
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/students/student-details?id={record.id}",
            )
        )

    page_numbers = list(range(1, min(total_pages, 12) + 1)) if total_pages else []
    if total_pages > 12:
        page_numbers = [1, 2, 3, -1, total_pages]

    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)

    programme_codes: set[str] = set()
    for record in records:
        if record.programme_code:
            programme_codes.add(record.programme_code.upper())
    programme_options = [UserListFilterOption(value="", label="Programme")]
    for code in sorted(programme_codes):
        prog = programme_by_code.get(code)
        programme_options.append(UserListFilterOption(value=code, label=prog.name if prog else code))

    sections = sorted({(r.section_code or "").strip().upper() for r in records if (r.section_code or "").strip()})
    section_options = [UserListFilterOption(value="", label="Section")]
    for sec in sections:
        section_options.append(UserListFilterOption(value=sec, label=sec))

    year_options = [UserListFilterOption(value="", label="Year")]
    year_options.extend(UserListFilterOption(value=str(n), label=f"Year {n}") for n in range(1, 5))
    year_options.append(UserListFilterOption(value="5", label="PG & Ph.D."))

    return AllStudentsListPageRead(
        page_title="All Students List",
        page_subtitle="Search and manage every student record in the college",
        export_label="Export",
        add_student_label="Add student",
        add_student_href="/college-admin/students/create-student",
        bulk_actions_label="Bulk actions",
        bulk_actions_href="/college-admin/students/bulk-student-import",
        search_placeholder="Search name, register number, phone or email...",
        programme_filter_label="Programme",
        year_filter_label="Year",
        section_filter_label="Section",
        status_filter_label="Status",
        programme_options=programme_options,
        year_options=year_options,
        section_options=section_options,
        status_options=[UserListFilterOption(value=v, label=lbl) for v, lbl in _STATUS_FILTERS],
        students_section_title="Students",
        students_count_label=f"{total:,} students",
        table_headers=["Student", "Register no.", "Programme", "Year / Sec", "Attendance", "Fee status", "Status"],
        students=table_rows,
        showing_label=f"Showing {showing_from}–{showing_to} of {total:,}" if total else "Showing 0 of 0",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=page_numbers,
            has_previous=page > 1 and bool(total),
            has_next=page < total_pages,
        ),
        footer_disclaimer="Live institutional data · Student, attendance and finance records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )