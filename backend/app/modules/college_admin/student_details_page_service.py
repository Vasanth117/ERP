"""Student details page (CA 06.03)."""

from __future__ import annotations

from zoneinfo import ZoneInfo

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
    _fee_presentation,
    _register_number,
    _student_status_code,
)
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    StudentDetailsBadge,
    StudentDetailsDocumentRow,
    StudentDetailsKeyValueRow,
    StudentDetailsPageRead,
    StudentDetailsStandingField,
)
from app.modules.college_admin.student_admin_models import (
    StudentAdmission,
    StudentGuardianRelationship,
    StudentRecord,
)
from app.modules.college_admin.student_statistics_overview_service import (
    _CATEGORY_LABELS,
    _meta_lookup,
    _normalize_meta_key,
)
from app.modules.finance.finance_models import StudentFeeDemand
from app.modules.students.enums import AcademicStanding
from app.modules.students.models import StudentAcademicRecord, StudentProfile

_IST = ZoneInfo("Asia/Kolkata")
_reader = OperationalDataReader()


def _initials(full_name: str) -> str:
    parts = [p for p in full_name.strip().split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return f"{parts[0][0]}{parts[-1][0]}".upper()


def _format_admitted(profile: StudentProfile | None, admission: StudentAdmission | None) -> str:
    if profile and profile.admission_date:
        return f"Admitted {profile.admission_date.strftime('%d %b %Y')}"
    if admission:
        local = as_utc_aware(admission.created_at).astimezone(_IST)
        return f"Admitted {local.strftime('%d %b %Y')}"
    return "Admitted —"


def _quota_badge(admission: StudentAdmission | None) -> StudentDetailsBadge | None:
    if admission is None:
        return None
    raw = _meta_lookup(admission.metadata, "quota", "admission_quota", "category", "seat_category")
    if not raw:
        return None
    key = _normalize_meta_key(raw)
    label = _CATEGORY_LABELS.get(key, raw.replace("_", " ").title())
    return StudentDetailsBadge(key="quota", label=label, tone="muted")


def _lifecycle_badge(record: StudentRecord, user: User, attendance_pct: float | None, min_attendance: float, standing: AcademicStanding | None) -> StudentDetailsBadge:
    _, label, tone = _student_status_code(record, user, attendance_pct=attendance_pct, min_attendance=min_attendance, standing=standing)
    return StudentDetailsBadge(key="lifecycle", label=label, tone=tone)


def _document_rows(profile: StudentProfile, admission: StudentAdmission | None) -> list[StudentDetailsDocumentRow]:
    rows: list[StudentDetailsDocumentRow] = []
    seen: set[str] = set()

    meta_docs = admission.metadata.get("documents") if admission else None
    if isinstance(meta_docs, list):
        for index, item in enumerate(meta_docs):
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or item.get("name") or item.get("type") or f"Document {index + 1}")
            key = _normalize_meta_key(label) or f"doc_{index}"
            if key in seen:
                continue
            seen.add(key)
            verified = item.get("verified") is True or item.get("status") in {"verified", "approved"}
            uploaded = item.get("uploaded_at") or item.get("uploaded_label")
            uploaded_label = str(uploaded)[:32] if uploaded else "—"
            verifier = item.get("verified_by_name") or item.get("verified_by") or "—"
            rows.append(
                StudentDetailsDocumentRow(
                    document_key=key,
                    document_label=label,
                    uploaded_label=uploaded_label,
                    status_label="Verified" if verified else "Pending",
                    status_tone="success" if verified else "warning",
                    verified_by_label=str(verifier) if verifier else "—",
                )
            )

    for ref in profile.document_refs:
        key = ref.document_type or ref.label
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            StudentDetailsDocumentRow(
                document_key=key,
                document_label=ref.label or ref.document_type,
                uploaded_label="—",
                status_label="Verified" if ref.authorized else "Pending",
                status_tone="success" if ref.authorized else "warning",
                verified_by_label="—",
            )
        )
    return rows


def _fee_standing_label(fee_label: str) -> tuple[str, str | None]:
    if fee_label == "Paid":
        return "Cleared", "success"
    if fee_label == "Overdue":
        return "Overdue", "error"
    if fee_label == "Partial":
        return "Partial", "warning"
    return fee_label, "muted"


async def get_student_details_page(scope: AccessScope, record_id_raw: str) -> StudentDetailsPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    record_id = to_object_id(record_id_raw, "record_id")
    now = utcnow()
    ay_label, semester_label = await _reader.current_academic_term(tenant_id)

    record = await StudentRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)

    user = await User.find_one(Eq(User.id, record.user_id), Eq(User.tenant_id, tenant_id))
    if user is None:
        raise AppError(code="NOT_FOUND", message="Student user not found", status_code=404)

    profile = await StudentProfile.find_one(
        Eq(StudentProfile.tenant_id, tenant_id),
        Eq(StudentProfile.user_id, record.user_id),
    )
    if profile is None:
        profile = StudentProfile(tenant_id=tenant_id, user_id=record.user_id)

    admission = await StudentAdmission.get(record.admission_id) if record.admission_id else None

    programme = None
    if record.programme_code:
        programme = await AcademicProgramme.find_one(
            Eq(AcademicProgramme.tenant_id, tenant_id),
            Eq(AcademicProgramme.programme_code, record.programme_code),
        )
    programme_label = (profile.programme_name or (programme.name if programme else None) or record.programme_code or "—")

    department_label = "—"
    if record.department_id:
        dept = await InstitutionDepartment.get(record.department_id)
        if dept:
            department_label = dept.name

    register_no = _register_number(record, profile)
    section = (record.section_code or profile.section_code or "—").strip() or "—"
    semester_display = semester_label or "—"
    academic_records = await StudentAcademicRecord.find(
        Eq(StudentAcademicRecord.tenant_id, tenant_id),
        Eq(StudentAcademicRecord.user_id, record.user_id),
    ).sort("-updated_at").to_list()
    if academic_records:
        semester_display = academic_records[0].semester_label or semester_display

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
    badges = [_lifecycle_badge(record, user, attendance_pct, min_attendance, standing)]
    quota = _quota_badge(admission)
    if quota:
        badges.append(quota)

    regulation_label = "—"
    if admission:
        regulation_label = _meta_lookup(
            admission.metadata,
            "regulation_label",
            "regulation",
            "regulation_code",
        ) or "—"

    enrollment_rows = [
        StudentDetailsKeyValueRow(key="programme", label="Programme", value=programme_label),
        StudentDetailsKeyValueRow(key="department", label="Department", value=department_label),
        StudentDetailsKeyValueRow(
            key="batch",
            label="Batch",
            value=(record.batch_label or profile.batch_label or "—").replace("-", "–"),
        ),
        StudentDetailsKeyValueRow(key="semester", label="Semester", value=str(semester_display)),
        StudentDetailsKeyValueRow(key="section", label="Section", value=section),
        StudentDetailsKeyValueRow(key="regulation", label="Regulation", value=regulation_label),
    ]

    document_rows = _document_rows(profile, admission)
    documents_footer_label = f"{len(document_rows)} document{'s' if len(document_rows) != 1 else ''}"

    guardians = await StudentGuardianRelationship.find(
        Eq(StudentGuardianRelationship.tenant_id, tenant_id),
        Eq(StudentGuardianRelationship.user_id, record.user_id),
    ).sort("-created_at").to_list()
    primary_guardian = guardians[0] if guardians else None
    phone = record.contact_phone or profile.contact_phone or "—"
    address = profile.current_address or profile.permanent_address or "—"

    contact_rows = [
        StudentDetailsKeyValueRow(key="mobile", label="Mobile", value=phone),
        StudentDetailsKeyValueRow(
            key="guardian",
            label="Guardian",
            value=primary_guardian.guardian_name if primary_guardian else "—",
        ),
        StudentDetailsKeyValueRow(
            key="guardian_mobile",
            label="Guardian mobile",
            value=primary_guardian.phone if primary_guardian else "—",
        ),
        StudentDetailsKeyValueRow(key="address", label="Address", value=address),
    ]

    fee_demands = await StudentFeeDemand.find(
        Eq(StudentFeeDemand.tenant_id, tenant_id),
        Eq(StudentFeeDemand.student_user_id, record.user_id),
    ).to_list()
    fee_label, fee_tone = _fee_presentation(fee_demands)
    fee_standing, fee_standing_tone = _fee_standing_label(fee_label)

    cgpa_val = "—"
    backlog_val = "—"
    if academic_records:
        ar = academic_records[0]
        if ar.cgpa is not None:
            cgpa_val = f"{ar.cgpa:.2f}"
        summary = ar.eligibility_summary or {}
        backlog = summary.get("backlog_count") or summary.get("backlogs")
        if isinstance(backlog, (int, float)):
            backlog_val = str(int(backlog))

    attendance_display = f"{attendance_pct:.0f}%" if attendance_pct is not None else "—"
    standing_fields = [
        StudentDetailsStandingField(key="cgpa", label="CGPA", value=cgpa_val),
        StudentDetailsStandingField(
            key="attendance",
            label="Attendance",
            value=attendance_display,
            value_tone="success" if attendance_pct is not None and attendance_pct >= min_attendance else "warning",
        ),
        StudentDetailsStandingField(key="backlogs", label="Backlogs", value=backlog_val),
        StudentDetailsStandingField(
            key="fee_status",
            label="Fee status",
            value=fee_standing,
            value_tone=fee_standing_tone,
        ),
    ]

    return StudentDetailsPageRead(
        page_title="Student Details",
        page_subtitle=f"Complete record for {user.full_name}",
        back_href="/college-admin/students/all-students-list",
        back_label="All students",
        record_id=str(record.id),
        edit_profile_label="Edit profile",
        edit_profile_href=f"/college-admin/students/student-profile-management?record_id={record.id}",
        academic_history_label="Academic history",
        academic_history_href=f"/college-admin/students/student-academic-history?id={record.id}",
        profile_initials=_initials(user.full_name),
        profile_name=user.full_name,
        profile_badges=badges,
        profile_summary_line=profile_summary_line,
        email=user.email,
        phone=phone,
        admitted_label=_format_admitted(profile, admission),
        enrollment_section_title="Enrollment",
        enrollment_rows=enrollment_rows,
        documents_section_title="Documents",
        documents_table_headers=["Document", "Uploaded", "Status", "Verified by"],
        document_rows=document_rows,
        documents_footer_label=documents_footer_label,
        contact_section_title="Contact and guardian",
        contact_rows=contact_rows,
        standing_section_title="Academic standing",
        standing_fields=standing_fields,
        footer_disclaimer="Live institutional data · Student, attendance and finance records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )