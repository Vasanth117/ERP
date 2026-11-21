"""Employee profile management (CA 07.06)."""

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
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import (
    EmployeeRecord,
    FacultyEmploymentHistory,
    FacultyEmploymentStatus,
    FacultyRecord,
)
from app.modules.college_admin.faculty_admin_service import _sync_employee_snapshot, _sync_faculty_profile
from app.modules.college_admin.faculty_employee_dashboard_page_service import _status_for_row
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    EmployeeProfileManagementFormValues,
    EmployeeProfileManagementLastUpdated,
    EmployeeProfileManagementLockedField,
    EmployeeProfileManagementPageRead,
    EmployeeProfileManagementSavePayload,
    EmployeeProfilePickerRow,
    InstitutionFieldMeta,
    StudentDetailsBadge,
)
from app.modules.faculty.models import FacultyProfile
from app.repositories.user_repository import UserRepository

_IST = ZoneInfo("Asia/Kolkata")
_USER_REPO = UserRepository()

_PROFILE_FIELD_META = [
    InstitutionFieldMeta(key="full_name", label="Full name", required=True),
    InstitutionFieldMeta(key="mobile", label="Mobile", required=True),
    InstitutionFieldMeta(key="official_email", label="Official email", required=True, field_type="email"),
    InstitutionFieldMeta(key="emergency_contact", label="Emergency contact"),
    InstitutionFieldMeta(key="address", label="Address", field_type="textarea"),
    InstitutionFieldMeta(key="reason_for_change", label="Reason for change", required=True, field_type="textarea"),
]


def _initials(full_name: str) -> str:
    parts = [p for p in full_name.strip().split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return f"{parts[0][0]}{parts[-1][0]}".upper()


def _joined_label(joining_date) -> str:
    if joining_date is None:
        return "Joined —"
    return f"Joined {joining_date.strftime('%d %b %Y')}"


def _format_ist_datetime(when) -> str:
    local = as_utc_aware(when).astimezone(_IST)
    return local.strftime("%d %b %Y, %H:%M IST")


def _coerce_form(raw: dict[str, Any]) -> EmployeeProfileManagementFormValues:
    return EmployeeProfileManagementFormValues(
        full_name=str(raw.get("full_name") or "").strip(),
        mobile=str(raw.get("mobile") or "").strip(),
        official_email=str(raw.get("official_email") or "").strip().lower(),
        emergency_contact=str(raw.get("emergency_contact") or "").strip(),
        address=str(raw.get("address") or "").strip(),
        reason_for_change=str(raw.get("reason_for_change") or "").strip(),
    )


def _employment_type_badge(employee: EmployeeRecord | None) -> tuple[str, str] | None:
    if employee is None:
        return None
    blob = (employee.employment_type or "").lower()
    if "permanent" in blob or employee.employment_status == FacultyEmploymentStatus.CONFIRMED:
        return "Permanent", "muted"
    if employee.is_faculty:
        return "Faculty", "muted"
    return (employee.employment_type or "Staff").title(), "muted"


async def _resolve_context(
    tenant_id: PydanticObjectId,
    record_id_raw: str,
) -> tuple[User, EmployeeRecord, FacultyRecord | None, FacultyProfile | None]:
    record_oid = to_object_id(record_id_raw, "record_id")

    faculty = await FacultyRecord.get(record_oid)
    if faculty and faculty.tenant_id == tenant_id:
        employee = await EmployeeRecord.find_one(
            Eq(EmployeeRecord.tenant_id, tenant_id),
            Eq(EmployeeRecord.user_id, faculty.user_id),
        )
        if employee is None:
            raise AppError(code="NOT_FOUND", message="Employee record not found", status_code=404)
        user = await User.get(faculty.user_id)
        if user is None or user.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
        profile = await FacultyProfile.find_one(
            Eq(FacultyProfile.tenant_id, tenant_id),
            Eq(FacultyProfile.user_id, faculty.user_id),
        )
        return user, employee, faculty, profile

    employee = await EmployeeRecord.get(record_oid)
    if employee is None or employee.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Employee record not found", status_code=404)
    user = await User.get(employee.user_id)
    if user is None or user.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    faculty = await FacultyRecord.find_one(
        Eq(FacultyRecord.tenant_id, tenant_id),
        Eq(FacultyRecord.user_id, employee.user_id),
    )
    profile = None
    if faculty:
        profile = await FacultyProfile.find_one(
            Eq(FacultyProfile.tenant_id, tenant_id),
            Eq(FacultyProfile.user_id, faculty.user_id),
        )
    return user, employee, faculty, profile


async def _build_page(
    scope: AccessScope,
    user: User,
    employee: EmployeeRecord,
    faculty: FacultyRecord | None,
    profile: FacultyProfile | None,
) -> EmployeeProfileManagementPageRead:
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    dept_name = "—"
    if employee.department_id:
        dept = await InstitutionDepartment.get(employee.department_id)
        if dept and dept.tenant_id == tenant_id:
            dept_name = dept.name or dept.department_code
    designation = employee.designation or (faculty.designation if faculty else None) or "—"
    emp_id = employee.employee_id or (faculty.faculty_code if faculty else None) or "—"
    profile_summary = f"{designation} · {dept_name} · {emp_id}"

    hr = employee.confidential_hr or {}
    mobile = (profile.contact_phone if profile else None) or hr.get("mobile") or ""
    address = hr.get("address") or ""
    emergency = hr.get("emergency_contact") or ""

    status_label, status_tone = _status_for_row(employment_status=employee.employment_status, workload_hours=None)
    badges = [StudentDetailsBadge(key="status", label=status_label, tone=status_tone)]
    type_badge = _employment_type_badge(employee)
    if type_badge:
        label, tone = type_badge
        badges.append(StudentDetailsBadge(key="employment_type", label=label, tone=tone))

    form = EmployeeProfileManagementFormValues(
        full_name=user.full_name,
        mobile=str(mobile),
        official_email=user.email,
        emergency_contact=str(emergency),
        address=str(address),
        reason_for_change="",
    )

    record_id = str(faculty.id) if faculty else str(employee.id)
    detail_href = (
        f"/college-admin/faculty/faculty-profile?id={faculty.id}"
        if faculty
        else f"/college-admin/faculty/employee-profile-management?id={employee.id}"
    )

    return EmployeeProfileManagementPageRead(
        page_title="Employee Profile Management",
        page_subtitle="Update an employee record",
        discard_label="Discard",
        save_changes_label="Save changes",
        requires_record=False,
        record_id=record_id,
        faculty_record_id=str(faculty.id) if faculty else None,
        detail_href=detail_href,
        profile_initials=_initials(user.full_name),
        profile_name=user.full_name,
        profile_badges=badges,
        profile_summary_line=profile_summary,
        email_display=user.email,
        phone_display=mobile or "—",
        joined_label=_joined_label(employee.joining_date),
        editable_section_title="Editable profile",
        field_meta=_PROFILE_FIELD_META,
        form=form,
        locked_fields_title="Controlled by HR",
        locked_fields=[
            EmployeeProfileManagementLockedField(label="Salary and payroll", subtitle="HR portal"),
            EmployeeProfileManagementLockedField(label="Leave balances", subtitle="HR portal"),
        ],
        last_updated_title="Last updated",
        last_updated=EmployeeProfileManagementLastUpdated(
            updated_by_label="College Admin",
            updated_at_label=_format_ist_datetime(employee.updated_at),
        ),
        audit_footer_note="Changes are saved with your name and reason for change.",
        footer_disclaimer="Live institutional data · Faculty and employee records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def get_employee_profile_management_page(
    scope: AccessScope,
    record_id_raw: str | None = None,
) -> EmployeeProfileManagementPageRead:
    authorize(scope, Permission.FACULTY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    if not record_id_raw or not record_id_raw.strip():
        employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).sort("-updated_at").limit(12).to_list()
        picker: list[EmployeeProfilePickerRow] = []
        for employee in employees:
            user = await User.get(employee.user_id)
            if user is None:
                continue
            picker.append(
                EmployeeProfilePickerRow(
                    record_id=str(employee.id),
                    employee_name=user.full_name,
                    employee_id_label=employee.employee_id or "—",
                    manage_href=f"/college-admin/faculty/employee-profile-management?id={employee.id}",
                )
            )
        return EmployeeProfileManagementPageRead(
            page_title="Employee Profile Management",
            page_subtitle="Update an employee record",
            discard_label="Discard",
            save_changes_label="Save changes",
            requires_record=True,
            select_employee_title="Select an employee to manage",
            select_employee_hint="Open a profile from the employee directory or pick a recent record below.",
            employee_directory_href="/college-admin/faculty/employee-directory",
            employee_directory_label="Employee directory",
            picker_rows=picker,
            audit_footer_note="Changes are saved with your name and reason for change.",
            footer_disclaimer="Live institutional data · Faculty and employee records · All times IST",
            footer_snapshot_label="Snapshot",
            generated_at=now,
        )

    user, employee, faculty, profile = await _resolve_context(tenant_id, record_id_raw)
    return await _build_page(scope, user, employee, faculty, profile)


async def save_employee_profile_management(
    scope: AccessScope,
    payload: EmployeeProfileManagementSavePayload,
) -> EmployeeProfileManagementPageRead:
    authorize(scope, Permission.FACULTY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    actor_id = scope.user_id
    assert actor_id is not None

    form = _coerce_form(payload.values)
    if not form.full_name or not form.mobile or not form.official_email:
        raise AppError(code="VALIDATION_ERROR", message="Full name, mobile and email are required", status_code=422)
    if not form.reason_for_change:
        raise AppError(code="VALIDATION_ERROR", message="Reason for change is required", status_code=422)

    user, employee, faculty, profile = await _resolve_context(tenant_id, payload.record_id)

    email = form.official_email.lower()
    if email != user.email.lower():
        existing = await _USER_REPO.find_by_email_in_tenant(email, tenant_id)
        if existing is not None and existing.id != user.id:
            raise AppError(code="CONFLICT", message="Another user already uses this email", status_code=409)
        user.email = email

    user.full_name = form.full_name
    user.updated_at = utcnow()
    await user.save()

    hr = dict(employee.confidential_hr or {})
    hr["mobile"] = form.mobile
    hr["address"] = form.address
    hr["emergency_contact"] = form.emergency_contact
    employee.confidential_hr = hr
    employee.updated_at = utcnow()
    employee.updated_by = actor_id
    await employee.save()
    await _sync_employee_snapshot(employee)

    if faculty:
        if profile is None:
            profile = FacultyProfile(tenant_id=tenant_id, user_id=faculty.user_id)
        profile.contact_phone = form.mobile
        profile.updated_at = utcnow()
        if profile.id is None:
            await profile.insert()
        else:
            await profile.save()
        await _sync_faculty_profile(faculty, user)

    await FacultyEmploymentHistory(
        tenant_id=tenant_id,
        user_id=user.id,
        event_type="profile_update",
        note=form.reason_for_change,
        actor_id=actor_id,
    ).insert()

    return await _build_page(scope, user, employee, faculty, profile)