"""Faculty timetable view (CA 07.10)."""

from __future__ import annotations

from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.mongo_time import _parse_time_value
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.academics.enums import SessionType
from app.modules.academics.models import TimetableEntry
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus, FacultyRecord
from app.modules.college_admin.faculty_employee_dashboard_page_service import _status_for_row
from app.modules.college_admin.faculty_profile_page_service import (
    _employment_type_label,
    _initials,
    _joined_label,
)
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    FacultyTimetableDayRow,
    FacultyTimetableGridCell,
    FacultyTimetableGridColumn,
    FacultyTimetablePageRead,
    FacultyTimetablePickerRow,
    StudentDetailsBadge,
)
from app.modules.faculty.integrations.academic_reader import AcademicDataReader
from app.modules.faculty.models import FacultyProfile, FacultyWorkload

_IST = ZoneInfo("Asia/Kolkata")
_reader = OperationalDataReader()
_academic = AcademicDataReader()
_DAY_LABELS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")


def _format_slot(start_raw: str, end_raw: str) -> str:
    start = _parse_time_value(start_raw)
    end = _parse_time_value(end_raw)
    return f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')}"


def _cell_label(entry: TimetableEntry) -> str:
    name = entry.course_name or entry.course_code
    section = entry.section
    if entry.session_type == SessionType.LABORATORY:
        return f"{name} Lab - {section}"
    if "meeting" in name.lower():
        return "Department meeting"
    if "mentor" in name.lower():
        return "Mentoring"
    if section and section != "—":
        return f"{name} - {section}"
    return name


def _duration_hours(start_raw: str, end_raw: str) -> float:
    start = _parse_time_value(start_raw)
    end = _parse_time_value(end_raw)
    delta = (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)
    return max(0.0, delta / 60.0)


async def _picker_rows(tenant_id) -> list[FacultyTimetablePickerRow]:
    faculty = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).sort("-updated_at").limit(16).to_list()
    rows: list[FacultyTimetablePickerRow] = []
    for record in faculty:
        user = await User.get(record.user_id)
        if user is None:
            continue
        employee = await EmployeeRecord.find_one(
            Eq(EmployeeRecord.tenant_id, tenant_id),
            Eq(EmployeeRecord.user_id, record.user_id),
        )
        emp_id = (employee.employee_id if employee else None) or record.faculty_code or "—"
        record_id = str(record.id)
        rows.append(
            FacultyTimetablePickerRow(
                record_id=record_id,
                faculty_name=user.full_name,
                employee_id_label=emp_id,
                timetable_href=f"/college-admin/faculty/faculty-timetable?id={record_id}",
            )
        )
    return rows


async def get_faculty_timetable_page(
    scope: AccessScope,
    record_id_raw: str | None = None,
    *,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> FacultyTimetablePageRead:
    authorize(scope, Permission.FACULTY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    year_label, sem_label = await _reader.current_academic_term(tenant_id)
    selected_year = academic_year_label or year_label or "2026–27"
    selected_semester = semester_label or sem_label or "Odd"

    if not record_id_raw or not record_id_raw.strip():
        return FacultyTimetablePageRead(
            page_title="Faculty Timetable",
            page_subtitle="Weekly teaching schedule",
            context_line=f"{selected_semester} {selected_year}",
            print_label="Print",
            edit_slots_label="Edit slots",
            edit_slots_href="/college-admin/faculty/faculty-subject-allocation",
            requires_record=True,
            select_faculty_title="Select a faculty member",
            select_faculty_hint="Open a faculty profile or pick from the list below.",
            faculty_directory_href="/college-admin/faculty/faculty-directory",
            faculty_directory_label="Faculty directory",
            picker_rows=await _picker_rows(tenant_id),
            column_headers=["Day"],
            time_columns=[],
            day_rows=[],
            timetable_footer_label="",
            footer_disclaimer="Live institutional data · Faculty and employee records · All times IST",
            footer_snapshot_label="Snapshot",
            generated_at=now,
        )

    record_oid = to_object_id(record_id_raw, "record_id")
    record = await FacultyRecord.get(record_oid)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Faculty record not found", status_code=404)
    user = await User.get(record.user_id)
    if user is None:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    employee = await EmployeeRecord.find_one(
        Eq(EmployeeRecord.tenant_id, tenant_id),
        Eq(EmployeeRecord.user_id, record.user_id),
    )
    profile = await FacultyProfile.find_one(
        Eq(FacultyProfile.tenant_id, tenant_id),
        Eq(FacultyProfile.user_id, record.user_id),
    )

    dept_name = "—"
    if record.department_id:
        dept = await InstitutionDepartment.get(record.department_id)
        if dept:
            dept_name = dept.name or dept.department_code
    emp_id = (employee.employee_id if employee else None) or record.faculty_code or "—"
    designation = record.designation or (profile.designation if profile else None) or "—"
    profile_summary = f"{designation} · {dept_name} · {emp_id}"

    status_label, status_tone = _status_for_row(employment_status=record.employment_status, workload_hours=None)
    badges = [StudentDetailsBadge(key="status", label=status_label, tone=status_tone)]
    if employee and employee.employment_type:
        badges.append(
            StudentDetailsBadge(
                key="employment_type",
                label=_employment_type_label(employee.employment_type),
                tone="muted",
            )
        )
    elif record.employment_status == FacultyEmploymentStatus.CONFIRMED:
        badges.append(StudentDetailsBadge(key="employment_type", label="Permanent", tone="info"))

    phone = "—"
    if profile and profile.contact_phone:
        phone = profile.contact_phone
    elif employee and isinstance(employee.confidential_hr, dict):
        phone = str(employee.confidential_hr.get("mobile") or employee.confidential_hr.get("phone") or "—")

    entries = await TimetableEntry.find(
        Eq(TimetableEntry.tenant_id, tenant_id),
        Eq(TimetableEntry.faculty_user_id, record.user_id),
        Eq(TimetableEntry.academic_year_label, selected_year),
        Eq(TimetableEntry.semester_label, selected_semester),
    ).to_list()
    if not entries:
        entries = await _academic.weekly_timetable(tenant_id, record.user_id)

    slot_keys: list[tuple[str, str, str]] = []
    for item in entries:
        key = (item.start_time, item.end_time)
        if key not in [(a, b, c) for a, b, c in slot_keys]:
            slot_keys.append((item.start_time, item.end_time, _format_slot(item.start_time, item.end_time)))
    slot_keys.sort(key=lambda row: _parse_time_value(row[0]))

    time_columns = [
        FacultyTimetableGridColumn(key=f"{start}-{end}", label=label) for start, end, label in slot_keys
    ]
    column_headers = ["Day", *[col.label for col in time_columns]]

    entry_index: dict[tuple[int, str, str], TimetableEntry] = {}
    for item in entries:
        if item.day_of_week > 4:
            continue
        entry_index[(item.day_of_week, item.start_time, item.end_time)] = item

    day_rows: list[FacultyTimetableDayRow] = []
    teaching_hours = 0.0
    free_slots = 0
    for day_index, day_label in enumerate(_DAY_LABELS):
        cells: list[FacultyTimetableGridCell] = []
        for start, end, _ in slot_keys:
            entry = entry_index.get((day_index, start, end))
            if entry is None:
                cells.append(FacultyTimetableGridCell(label="—", is_empty=True))
                free_slots += 1
            else:
                label = _cell_label(entry)
                cells.append(FacultyTimetableGridCell(label=label, is_empty=False))
                teaching_hours += _duration_hours(entry.start_time, entry.end_time)
        day_rows.append(
            FacultyTimetableDayRow(day_key=str(day_index), day_label=day_label, cells=cells),
        )

    workload = await FacultyWorkload.find_one(
        Eq(FacultyWorkload.tenant_id, tenant_id),
        Eq(FacultyWorkload.user_id, record.user_id),
        Eq(FacultyWorkload.academic_year_label, selected_year),
        Eq(FacultyWorkload.semester_label, selected_semester),
    )
    if workload and workload.total_hours > 0:
        teaching_hours = workload.total_hours

    footer = f"{int(round(teaching_hours))} teaching hours · {free_slots} free hours"
    context_line = f"{user.full_name} · {selected_semester} {selected_year}"

    return FacultyTimetablePageRead(
        page_title="Faculty Timetable",
        page_subtitle="Weekly teaching schedule",
        context_line=context_line,
        print_label="Print",
        edit_slots_label="Edit slots",
        edit_slots_href="/college-admin/faculty/faculty-subject-allocation",
        record_id=str(record.id),
        profile_initials=_initials(user.full_name),
        profile_name=user.full_name,
        profile_badges=badges,
        profile_summary_line=profile_summary,
        email_display=user.email,
        phone_display=phone,
        joined_label=_joined_label(employee.joining_date if employee else None),
        weekly_section_title="Weekly timetable",
        column_headers=column_headers,
        time_columns=time_columns,
        day_rows=day_rows,
        timetable_footer_label=footer,
        footer_disclaimer="Live institutional data · Faculty and employee records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )