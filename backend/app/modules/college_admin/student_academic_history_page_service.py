"""Student academic history page (CA 06.15 — History tab)."""

from __future__ import annotations

import re
from datetime import datetime

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.attendance.models import AttendancePolicyReference, AttendanceRecord
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.all_students_list_page_service import (
    _attendance_pct,
    _register_number,
    _student_status_code,
)
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    StudentAcademicHistoryChangeStep,
    StudentAcademicHistoryPageRead,
    StudentAcademicHistorySemesterRow,
    StudentDetailsBadge,
)
from app.modules.college_admin.student_admin_models import (
    StudentAdmission,
    StudentPromotionRecord,
    StudentRecord,
    StudentStatusHistory,
    StudentTransfer,
    TransferStatus,
)
from app.modules.college_admin.student_details_page_service import (
    _format_admitted,
    _initials,
    _quota_badge,
)
from app.modules.students.enums import ProgressionStatus, StudentEnrollmentStatus
from app.modules.students.models import StudentAcademicRecord, StudentProfile
from app.modules.students.student_portal_enums import StudentDocumentRequestStatus
from app.modules.students.student_portal_models import StudentProfileCorrectionRequest

_IST = __import__("zoneinfo").ZoneInfo("Asia/Kolkata")
_reader = OperationalDataReader()
_CORRECTION_LABELS = {
    "mobile": "Mobile number updated",
    "contact_phone": "Mobile number updated",
    "section_code": "Section changed",
    "roll_number": "Register number updated",
    "programme_name": "Programme updated",
}


def _short_date(value: datetime) -> str:
    local = as_utc_aware(value).astimezone(_IST)
    return local.strftime("%d %b %Y")


def _semester_sort_key(record: StudentAcademicRecord) -> tuple[str, int]:
    year = record.academic_year_label or ""
    match = re.search(r"\d+", record.semester_label or "")
    sem_num = int(match.group()) if match else 0
    return year, sem_num


def _semester_display_label(record: StudentAcademicRecord) -> str:
    match = re.search(r"\d+", record.semester_label or "")
    if match:
        return f"Semester {match.group()}"
    return record.semester_label or "Semester —"


def _year_display(year_label: str) -> str:
    return year_label.replace("-", "–") if year_label else "—"


def _term_sgpa(record: StudentAcademicRecord) -> float | None:
    summary = record.eligibility_summary or {}
    for key in ("sgpa", "term_gpa", "gpa", "semester_gpa"):
        raw = summary.get(key)
        if isinstance(raw, (int, float)):
            return round(float(raw), 2)
    if record.cgpa is not None:
        return round(float(record.cgpa), 2)
    return None


def _term_attendance(summary: dict, overall: float | None) -> str:
    raw = summary.get("attendance_percent") or summary.get("attendance_pct") or summary.get("attendance")
    if isinstance(raw, (int, float)):
        return f"{float(raw):.0f}%"
    if overall is not None:
        return f"{overall:.0f}%"
    return "—"


def _result_presentation(record: StudentAcademicRecord) -> tuple[str, str]:
    if record.enrollment_status == StudentEnrollmentStatus.COMPLETED:
        return "Pass", "success"
    if record.progression_status == ProgressionStatus.PROMOTED:
        return "Pass", "success"
    if record.progression_status in (ProgressionStatus.HELD, ProgressionStatus.REPEAT):
        return "Held", "warning"
    if record.progression_status == ProgressionStatus.PENDING:
        return "In progress", "info"
    summary = record.eligibility_summary or {}
    if summary.get("result") in ("pass", "Pass"):
        return "Pass", "success"
    if summary.get("result") in ("fail", "Fail"):
        return "Fail", "error"
    if record.credits_earned > 0:
        return "Pass", "success"
    return "—", "muted"


def _build_semester_rows(
    records: list[StudentAcademicRecord],
    overall_attendance: float | None,
) -> tuple[list[StudentAcademicHistorySemesterRow], int, float | None]:
    sorted_records = sorted(records, key=_semester_sort_key, reverse=True)
    rows: list[StudentAcademicHistorySemesterRow] = []
    completed = 0
    cgpa_values: list[float] = []
    for term in sorted_records:
        sgpa = _term_sgpa(term)
        if sgpa is not None:
            cgpa_values.append(sgpa)
        result_label, result_tone = _result_presentation(term)
        if result_label == "Pass":
            completed += 1
        credits = int(term.credits_earned) if term.credits_earned else int(term.credits_registered or 0)
        rows.append(
            StudentAcademicHistorySemesterRow(
                term_key=f"{term.academic_year_label}::{term.semester_label}",
                semester_label=_semester_display_label(term),
                year_label=_year_display(term.academic_year_label),
                sgpa_label=f"{sgpa:.2f}" if sgpa is not None else "—",
                credits_label=str(credits),
                result_label=result_label,
                result_tone=result_tone,
                attendance_label=_term_attendance(term.eligibility_summary or {}, overall_attendance),
            )
        )
    aggregate_cgpa = None
    if sorted_records and sorted_records[0].cgpa is not None:
        aggregate_cgpa = round(float(sorted_records[0].cgpa), 2)
    elif cgpa_values:
        aggregate_cgpa = round(sum(cgpa_values) / len(cgpa_values), 2)
    return rows, completed, aggregate_cgpa


async def _record_change_timeline(
    tenant_id,
    record: StudentRecord,
    user: User,
    profile: StudentProfile | None,
    admission: StudentAdmission | None,
) -> list[StudentAcademicHistoryChangeStep]:
    events: list[tuple[datetime, str, str, str]] = []

    if admission:
        events.append((admission.created_at, "admitted", "Admitted", "success"))
    elif profile and profile.admission_date:
        events.append((datetime.combine(profile.admission_date, datetime.min.time()), "admitted", "Admitted", "success"))

    promotions = await StudentPromotionRecord.find(
        Eq(StudentPromotionRecord.tenant_id, tenant_id),
        Eq(StudentPromotionRecord.user_id, record.user_id),
    ).sort("-created_at").to_list()
    for row in promotions:
        label = f"Promoted · {row.decision.replace('_', ' ').title()}"
        events.append((row.created_at, f"promo-{row.id}", label, "info"))

    transfers = await StudentTransfer.find(
        Eq(StudentTransfer.tenant_id, tenant_id),
        Eq(StudentTransfer.user_id, record.user_id),
        Eq(StudentTransfer.status, TransferStatus.COMPLETED),
    ).sort("-created_at").to_list()
    for row in transfers:
        events.append((row.completed_at or row.created_at, f"trf-{row.id}", "Transfer completed", "info"))

    status_rows = await StudentStatusHistory.find(
        Eq(StudentStatusHistory.tenant_id, tenant_id),
        Eq(StudentStatusHistory.user_id, record.user_id),
    ).sort("-created_at").to_list()
    for row in status_rows:
        label = f"Status changed to {row.to_status.replace('_', ' ').title()}"
        events.append((row.created_at, f"st-{row.id}", label, "warning"))

    corrections = await StudentProfileCorrectionRequest.find(
        Eq(StudentProfileCorrectionRequest.tenant_id, tenant_id),
        Eq(StudentProfileCorrectionRequest.user_id, record.user_id),
        Eq(StudentProfileCorrectionRequest.status, StudentDocumentRequestStatus.APPROVED),
    ).sort("-updated_at").to_list()
    for row in corrections:
        label = _CORRECTION_LABELS.get(row.field_name, f"{row.field_name.replace('_', ' ').title()} updated")
        if row.field_name == "section_code" and row.proposed_value:
            label = f"Section changed to {row.proposed_value}"
        events.append((row.updated_at, f"corr-{row.id}", label, "info"))

    if record.section_code and profile and profile.section_code != record.section_code:
        events.append((record.updated_at, "section-sync", f"Section {record.section_code}", "info"))

    events.sort(key=lambda item: item[0], reverse=True)
    return [
        StudentAcademicHistoryChangeStep(
            key=key,
            label=label,
            date_label=_short_date(at),
            tone=tone,
        )
        for at, key, label, tone in events
    ]


async def get_student_academic_history_page(
    scope: AccessScope,
    *,
    record_id: str | None = None,
) -> StudentAcademicHistoryPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    if not record_id:
        return StudentAcademicHistoryPageRead(
            page_title="Student Academic History",
            page_subtitle="Semester results and changes of record",
            back_href="/college-admin/students/all-students-list",
            back_label="All students",
            export_label="Export",
            selected_record_id="",
            profile_initials="?",
            profile_name="",
            profile_badges=[],
            profile_summary_line="",
            email="",
            phone="",
            admitted_label="",
            semester_record_section_title="Semester record",
            semester_table_headers=["Semester", "Year", "SGPA", "Credits", "Result", "Attendance"],
            semester_rows=[],
            semester_footer_label="0 of 0 completed",
            record_changes_section_title="Record changes",
            record_change_steps=[],
            footer_disclaimer="Live institutional data · Academic history and audit trail · All times IST",
            footer_snapshot_label="Snapshot",
            generated_at=now,
        )

    rid = to_object_id(record_id, "record_id")
    record = await StudentRecord.get(rid)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)

    user = await User.find_one(Eq(User.id, record.user_id), Eq(User.tenant_id, tenant_id))
    if user is None:
        raise AppError(code="NOT_FOUND", message="Student user not found", status_code=404)

    profile = await StudentProfile.find_one(
        Eq(StudentProfile.tenant_id, tenant_id),
        Eq(StudentProfile.user_id, record.user_id),
    )
    admission = await StudentAdmission.get(record.admission_id) if record.admission_id else None

    programme = None
    if record.programme_code:
        programme = await AcademicProgramme.find_one(
            Eq(AcademicProgramme.tenant_id, tenant_id),
            Eq(AcademicProgramme.programme_code, record.programme_code),
        )
    programme_label = (profile.programme_name if profile else None) or (programme.name if programme else None) or record.programme_code or "—"

    register_no = _register_number(record, profile)
    section = (record.section_code or (profile.section_code if profile else None) or "—").strip() or "—"
    ay_label, semester_label = await _reader.current_academic_term(tenant_id)
    academic_records = await StudentAcademicRecord.find(
        Eq(StudentAcademicRecord.tenant_id, tenant_id),
        Eq(StudentAcademicRecord.user_id, record.user_id),
    ).to_list()
    if academic_records:
        sem_disp = academic_records[0].semester_label
        match = re.search(r"\d+", sem_disp or "")
        semester_display = match.group() if match else (semester_label or "—")
    else:
        match = re.search(r"\d+", semester_label or "")
        semester_display = match.group() if match else (semester_label or "—")

    profile_summary_line = f"{register_no} · {programme_label} · Semester {semester_display} · Section {section}"

    policy = await AttendancePolicyReference.find_one(
        Eq(AttendancePolicyReference.tenant_id, tenant_id),
        Eq(AttendancePolicyReference.is_active, True),
    )
    min_attendance = policy.rules.min_percentage_required if policy else 75.0
    attendance_rows = await AttendanceRecord.find(
        Eq(AttendanceRecord.tenant_id, tenant_id),
        Eq(AttendanceRecord.student_user_id, record.user_id),
    ).to_list()
    attendance_pct = _attendance_pct(attendance_rows)

    standing = academic_records[0].academic_standing if academic_records else None
    status_code, status_label, status_tone = _student_status_code(
        record, user, attendance_pct=attendance_pct, min_attendance=min_attendance, standing=standing
    )
    badges = [StudentDetailsBadge(key="lifecycle", label=status_label, tone=status_tone)]
    quota = _quota_badge(admission)
    if quota:
        badges.append(quota)

    semester_rows, completed, aggregate_cgpa = _build_semester_rows(academic_records, attendance_pct)
    total_terms = len(semester_rows)
    footer_parts = [f"{completed} of {total_terms} completed"]
    if aggregate_cgpa is not None:
        footer_parts.append(f"CGPA {aggregate_cgpa:.2f}")
    semester_footer = " · ".join(footer_parts) if total_terms else "0 of 0 completed"

    timeline = await _record_change_timeline(tenant_id, record, user, profile, admission)

    phone = record.contact_phone or (profile.contact_phone if profile else None) or "—"

    return StudentAcademicHistoryPageRead(
        page_title="Student Academic History",
        page_subtitle="Semester results and changes of record",
        back_href="/college-admin/students/all-students-list",
        back_label="All students",
        export_label="Export",
        selected_record_id=str(record.id),
        profile_initials=_initials(user.full_name),
        profile_name=user.full_name,
        profile_badges=badges,
        profile_summary_line=profile_summary_line,
        email=user.email,
        phone=phone,
        admitted_label=_format_admitted(profile, admission),
        semester_record_section_title="Semester record",
        semester_table_headers=["Semester", "Year", "SGPA", "Credits", "Result", "Attendance"],
        semester_rows=semester_rows,
        semester_footer_label=semester_footer,
        record_changes_section_title="Record changes",
        record_change_steps=timeline,
        footer_disclaimer="Live institutional data · Academic history and audit trail · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )