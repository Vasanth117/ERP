"""Student profile management (CA 06 — Profiles & documents)."""

from __future__ import annotations

from typing import Any
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
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
from app.modules.college_admin.all_students_list_page_service import _attendance_pct, _register_number
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    InstitutionFieldMeta,
    StudentDetailsBadge,
    StudentProfileManagementFormValues,
    StudentProfileManagementLastUpdated,
    StudentProfileManagementLockedField,
    StudentProfileManagementPageRead,
    StudentProfileManagementSavePayload,
    StudentProfilePickerRow,
)
from app.modules.college_admin.student_admin_models import (
    StudentAdmission,
    StudentGuardianRelationship,
    StudentRecord,
    StudentStatusHistory,
)
from app.modules.college_admin.student_admin_service import _sync_profile
from app.modules.college_admin.student_details_page_service import (
    _format_admitted,
    _initials,
    _lifecycle_badge,
    _quota_badge,
)
from app.modules.students.enums import AcademicStanding
from app.modules.students.models import StudentAcademicRecord, StudentProfile
from app.repositories.user_repository import UserRepository

_IST = ZoneInfo("Asia/Kolkata")
_reader = OperationalDataReader()
_user_repo = UserRepository()

_PROFILE_FIELD_META = [
    InstitutionFieldMeta(key="full_name", label="Full name", required=True),
    InstitutionFieldMeta(key="mobile", label="Mobile", required=True),
    InstitutionFieldMeta(key="email", label="Email", required=True, field_type="email"),
    InstitutionFieldMeta(key="guardian_mobile", label="Guardian mobile", required=True),
    InstitutionFieldMeta(key="address", label="Address", field_type="textarea"),
    InstitutionFieldMeta(key="reason_for_change", label="Reason for change", required=True, field_type="textarea"),
]


def _format_ist_datetime(when) -> str:
    local = as_utc_aware(when).astimezone(_IST)
    return local.strftime("%d %b %Y %H:%M").replace(" 0", " ")


async def _updater_label(user_id: PydanticObjectId | None) -> str:
    if user_id is None:
        return "—"
    user = await User.get(user_id)
    if user is None:
        return "—"
    if user.role.value == "college_admin":
        return "College Admin"
    return user.full_name or "Staff"


def _coerce_form(raw: dict[str, Any]) -> StudentProfileManagementFormValues:
    return StudentProfileManagementFormValues(
        full_name=str(raw.get("full_name") or "").strip(),
        mobile=str(raw.get("mobile") or "").strip(),
        email=str(raw.get("email") or "").strip().lower(),
        guardian_mobile=str(raw.get("guardian_mobile") or "").strip(),
        address=str(raw.get("address") or "").strip(),
        reason_for_change=str(raw.get("reason_for_change") or "").strip(),
    )


async def _load_record_context(
    tenant_id: PydanticObjectId,
    record_id: PydanticObjectId,
) -> tuple[StudentRecord, User, StudentProfile, StudentAdmission | None]:
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
    return record, user, profile, admission


async def _build_profile_page(
    scope: AccessScope,
    record: StudentRecord,
    user: User,
    profile: StudentProfile,
    admission: StudentAdmission | None,
) -> StudentProfileManagementPageRead:
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    _, semester_label = await _reader.current_academic_term(tenant_id)

    programme_label = profile.programme_name or record.programme_code or "—"
    if record.programme_code:
        programme = await AcademicProgramme.find_one(
            Eq(AcademicProgramme.tenant_id, tenant_id),
            Eq(AcademicProgramme.programme_code, record.programme_code),
        )
        if programme and programme.name:
            programme_label = programme.name

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
    standing = academic_records[0].academic_standing if academic_records else AcademicStanding.UNKNOWN

    badges: list[StudentDetailsBadge] = [_lifecycle_badge(record, user, attendance_pct, min_attendance, standing)]
    quota = _quota_badge(admission)
    if quota:
        badges.append(quota)

    guardians = await StudentGuardianRelationship.find(
        Eq(StudentGuardianRelationship.tenant_id, tenant_id),
        Eq(StudentGuardianRelationship.user_id, record.user_id),
    ).sort("-created_at").to_list()
    primary_guardian = guardians[0] if guardians else None

    phone = record.contact_phone or profile.contact_phone or ""
    address = profile.current_address or profile.permanent_address or ""
    guardian_mobile = primary_guardian.phone if primary_guardian else ""

    batch_label = (record.batch_label or profile.batch_label or "—").replace("-", "–")
    programme_batch = f"{programme_label} · {batch_label}"

    form = StudentProfileManagementFormValues(
        full_name=user.full_name,
        mobile=phone,
        email=user.email,
        guardian_mobile=guardian_mobile,
        address=address,
        reason_for_change="",
    )

    return StudentProfileManagementPageRead(
        page_title="Student Profile Management",
        page_subtitle="Update student records with an audit trail",
        discard_label="Discard",
        save_changes_label="Save changes",
        requires_record=False,
        record_id=str(record.id),
        detail_href=f"/college-admin/students/student-details?id={record.id}",
        profile_initials=_initials(user.full_name),
        profile_name=user.full_name,
        profile_badges=badges,
        profile_summary_line=profile_summary_line,
        email_display=user.email,
        phone_display=phone or "—",
        admitted_label=_format_admitted(profile, admission),
        editable_section_title="Editable profile",
        field_meta=_PROFILE_FIELD_META,
        form=form,
        locked_fields_title="Locked fields",
        locked_fields=[
            StudentProfileManagementLockedField(
                key="register_number",
                label="Register number",
                value=register_no,
                hint="Cannot be changed",
            ),
            StudentProfileManagementLockedField(
                key="programme_batch",
                label="Programme and batch",
                value=programme_batch,
                hint="Use transfer workflow",
            ),
        ],
        transfer_workflow_href="/college-admin/students/student-transfer-management",
        last_updated_title="Last updated",
        last_updated=StudentProfileManagementLastUpdated(
            by_label=await _updater_label(record.updated_by),
            on_label=_format_ist_datetime(record.updated_at),
        ),
        document_verification_href=(
            f"/college-admin/students/student-document-verification?record_id={record.id}"
        ),
        audit_footer_note="Changes are saved to the audit log with your name and reason for change.",
        footer_disclaimer="Live institutional data · Student profile and contact records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def get_student_profile_management_page(
    scope: AccessScope,
    record_id_raw: str | None = None,
) -> StudentProfileManagementPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    if not record_id_raw or not record_id_raw.strip():
        records = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).sort("-updated_at").limit(12).to_list()
        picker: list[StudentProfilePickerRow] = []
        for record in records:
            user = await User.get(record.user_id)
            if user is None:
                continue
            profile = await StudentProfile.find_one(
                Eq(StudentProfile.tenant_id, tenant_id),
                Eq(StudentProfile.user_id, record.user_id),
            )
            picker.append(
                StudentProfilePickerRow(
                    record_id=str(record.id),
                    student_name=user.full_name,
                    register_number=_register_number(record, profile),
                    manage_href=f"/college-admin/students/student-profile-management?record_id={record.id}",
                )
            )
        return StudentProfileManagementPageRead(
            page_title="Student Profile Management",
            page_subtitle="Update student records with an audit trail",
            discard_label="Discard",
            save_changes_label="Save changes",
            requires_record=True,
            select_student_title="Select a student to manage",
            select_student_hint="Open a profile from the list below or search in All students.",
            all_students_href="/college-admin/students/all-students-list",
            all_students_label="All students",
            picker_rows=picker,
            audit_footer_note="Changes are saved to the audit log with your name and reason for change.",
            footer_disclaimer="Live institutional data · Student profile and contact records · All times IST",
            footer_snapshot_label="Snapshot",
            generated_at=now,
        )

    record_id = to_object_id(record_id_raw, "record_id")
    record, user, profile, admission = await _load_record_context(tenant_id, record_id)
    return await _build_profile_page(scope, record, user, profile, admission)


async def save_student_profile_management(
    scope: AccessScope,
    payload: StudentProfileManagementSavePayload,
) -> StudentProfileManagementPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    record_id = to_object_id(payload.record_id, "record_id")
    form = _coerce_form(payload.values)

    if not form.full_name or not form.mobile or not form.email:
        raise AppError(code="VALIDATION_ERROR", message="Full name, mobile and email are required", status_code=422)
    if not form.reason_for_change:
        raise AppError(code="VALIDATION_ERROR", message="Reason for change is required", status_code=422)

    record, user, profile, admission = await _load_record_context(tenant_id, record_id)

    email = form.email.lower()
    if email != user.email.lower():
        existing = await _user_repo.find_by_email_in_tenant(email, tenant_id)
        if existing is not None and existing.id != user.id:
            raise AppError(code="CONFLICT", message="Another user already uses this email", status_code=409)
        user.email = email

    user.full_name = form.full_name
    user.updated_at = utcnow()
    await user.save()

    record.contact_phone = form.mobile
    record.updated_at = utcnow()
    record.updated_by = scope.user_id
    await record.save()

    profile.contact_phone = form.mobile
    if form.address:
        profile.current_address = form.address
    profile.updated_at = utcnow()
    if profile.id is None:
        await profile.insert()
    else:
        await profile.save()

    guardian = await StudentGuardianRelationship.find_one(
        Eq(StudentGuardianRelationship.tenant_id, tenant_id),
        Eq(StudentGuardianRelationship.user_id, record.user_id),
    )
    if guardian and form.guardian_mobile:
        guardian.phone = form.guardian_mobile
        guardian.updated_at = utcnow()
        await guardian.save()
    elif form.guardian_mobile:
        await StudentGuardianRelationship(
            tenant_id=tenant_id,
            user_id=record.user_id,
            guardian_name="Primary guardian",
            relationship="guardian",
            phone=form.guardian_mobile,
        ).insert()

    await _sync_profile(record, user)

    await StudentStatusHistory(
        tenant_id=tenant_id,
        student_record_id=record.id,
        user_id=record.user_id,
        from_status="profile",
        to_status="profile_updated",
        reason=form.reason_for_change,
        actor_id=scope.user_id,
    ).insert()

    from app.modules.audit.service import record_audit

    await record_audit(
        actor_id=scope.user_id,
        action="student.profile.updated",
        resource_type="student_record",
        resource_id=str(record.id),
        tenant_id=tenant_id,
        metadata={
            "reason": form.reason_for_change,
            "full_name": user.full_name,
        },
    )

    record = await StudentRecord.get(record_id)
    assert record is not None
    user = await User.get(record.user_id)
    assert user is not None
    profile = await StudentProfile.find_one(
        Eq(StudentProfile.tenant_id, tenant_id),
        Eq(StudentProfile.user_id, record.user_id),
    )
    if profile is None:
        profile = StudentProfile(tenant_id=tenant_id, user_id=record.user_id)
    admission = await StudentAdmission.get(record.admission_id) if record.admission_id else None
    return await _build_profile_page(scope, record, user, profile, admission)