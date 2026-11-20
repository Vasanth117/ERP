"""Edit user information (CA 03.04)."""

from __future__ import annotations

from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.college_admin.identity_models import (
    InstitutionAccessHistory,
    InstitutionAccountStatus,
    InstitutionUser,
    InstitutionUserInvitation,
    InvitationStatus,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    EditUserAccountStatusCard,
    EditUserDangerAction,
    EditUserInformationFormValues,
    EditUserInformationPageRead,
    EditUserInformationSavePayload,
    InstitutionFieldMeta,
    InstitutionFieldOption,
)
from app.modules.college_admin.security_admin_models import InstitutionSecurityPolicy
from app.modules.college_admin.user_all_users_list_page_service import (
    _resolve_public_id,
    _status_presentation,
)
from app.modules.college_admin.user_details_page_service import _format_ist_date, _username_from_email
from app.modules.students.models import StudentProfile
from app.modules.tenants.models import Department
from app.repositories.user_repository import UserRepository

_user_repo = UserRepository()

_PROFILE_FIELD_META = [
    InstitutionFieldMeta(key="full_name", label="Full name", required=True),
    InstitutionFieldMeta(key="display_name", label="Display name"),
    InstitutionFieldMeta(key="official_email", label="Official email", required=True, field_type="email"),
    InstitutionFieldMeta(key="personal_email", label="Personal email", field_type="email"),
    InstitutionFieldMeta(key="mobile_number", label="Mobile number", required=True),
    InstitutionFieldMeta(key="alternate_phone", label="Alternate phone"),
    InstitutionFieldMeta(key="department_id", label="Department", required=True, field_type="select"),
    InstitutionFieldMeta(key="designation", label="Designation", required=True, field_type="select"),
]

_LOGIN_FIELD_META = [
    InstitutionFieldMeta(key="username", label="Username", locked=True),
    InstitutionFieldMeta(key="login_method", label="Login method", required=True, field_type="select"),
    InstitutionFieldMeta(key="mfa_requirement", label="MFA requirement", required=True, field_type="select"),
    InstitutionFieldMeta(key="session_timeout_minutes", label="Session timeout", field_type="select"),
]

_LOGIN_METHOD_OPTIONS = [
    InstitutionFieldOption(value="email_password", label="College account (email & password)"),
    InstitutionFieldOption(value="sso_google", label="College SSO (Google Workspace)"),
]

_MFA_OPTIONS = [
    InstitutionFieldOption(value="required", label="Required"),
    InstitutionFieldOption(value="optional", label="Optional"),
    InstitutionFieldOption(value="exempt", label="Exempt"),
]

_BASE_DESIGNATIONS = [
    "Professor",
    "Associate Professor",
    "Assistant Professor",
    "Lecturer",
    "Professor & Head",
    "Administrative Officer",
    "Student",
]


def _session_timeout_options(default_minutes: int) -> list[InstitutionFieldOption]:
    candidates = sorted({15, 30, 45, 60, 90, 120, default_minutes})
    return [InstitutionFieldOption(value=str(m), label=f"{m} minutes") for m in candidates]


def _coerce_edit_form(raw: dict[str, Any]) -> EditUserInformationFormValues:
    timeout = raw.get("session_timeout_minutes", 60)
    if isinstance(timeout, str) and timeout.isdigit():
        timeout = int(timeout)
    if not isinstance(timeout, int):
        timeout = 60
    return EditUserInformationFormValues(
        full_name=str(raw.get("full_name") or "").strip(),
        display_name=(str(raw.get("display_name")).strip() if raw.get("display_name") else None),
        official_email=str(raw.get("official_email") or "").strip().lower(),
        personal_email=(str(raw.get("personal_email")).strip() if raw.get("personal_email") else None),
        mobile_number=(str(raw.get("mobile_number")).strip() if raw.get("mobile_number") else None),
        alternate_phone=(str(raw.get("alternate_phone")).strip() if raw.get("alternate_phone") else None),
        department_id=raw.get("department_id") or None,
        designation=(str(raw.get("designation")).strip() if raw.get("designation") else None),
        username=str(raw.get("username") or ""),
        login_method=str(raw.get("login_method") or "email_password"),
        mfa_requirement=str(raw.get("mfa_requirement") or "required"),
        session_timeout_minutes=timeout,
    )


async def _load_user_context(
    scope: AccessScope,
    user_id: PydanticObjectId,
) -> tuple[User, InstitutionUser, EmployeeRecord | None, StudentProfile | None, str, str, str]:
    tenant_id = require_college_tenant_scope(scope)
    user = await User.find_one(Eq(User.id, user_id), Eq(User.tenant_id, tenant_id))
    if user is None:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    institution = await InstitutionUser.find_one(
        Eq(InstitutionUser.tenant_id, tenant_id),
        Eq(InstitutionUser.user_id, user_id),
    )
    if institution is None:
        from app.modules.college_admin.user_management_service import _ensure_institution_user

        institution = await _ensure_institution_user(tenant_id, user_id, department_id=user.department_id)
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, user_id))
    student = await StudentProfile.find_one(Eq(StudentProfile.tenant_id, tenant_id), Eq(StudentProfile.user_id, user_id))
    public_id = _resolve_public_id(user, student, employee)
    pending = await InstitutionUserInvitation.find_one(
        Eq(InstitutionUserInvitation.tenant_id, tenant_id),
        Eq(InstitutionUserInvitation.email, user.email),
        Eq(InstitutionUserInvitation.status, InvitationStatus.PENDING),
    )
    invited = pending is not None
    _, status_label, status_tone = _status_presentation(institution.account_status, invited)
    return user, institution, employee, student, public_id, status_label, status_tone


async def get_edit_user_information_page(scope: AccessScope, user_id: PydanticObjectId) -> EditUserInformationPageRead:
    authorize(scope, Permission.INSTITUTION_USER_READ)
    tenant_id = require_college_tenant_scope(scope)
    user, institution, employee, student, public_id, status_label, status_tone = await _load_user_context(scope, user_id)

    policy = await InstitutionSecurityPolicy.find_one(
        Eq(InstitutionSecurityPolicy.tenant_id, tenant_id),
        Eq(InstitutionSecurityPolicy.policy_id, "default"),
    )
    default_session = policy.session_max_idle_minutes if policy else 60

    departments = await Department.find(Eq(Department.tenant_id, tenant_id)).sort("+name").to_list()
    dept_options = [InstitutionFieldOption(value="", label="Select department")]
    dept_options.extend(InstitutionFieldOption(value=str(d.id), label=d.name) for d in departments)

    designations: set[str] = set(_BASE_DESIGNATIONS)
    if employee and employee.designation:
        designations.add(employee.designation)
    designation_options = [InstitutionFieldOption(value="", label="Select designation")]
    designation_options.extend(
        InstitutionFieldOption(value=name, label=name) for name in sorted(designations, key=str.lower)
    )

    hr = employee.confidential_hr if employee else {}
    mobile = student.contact_phone if student and student.contact_phone else hr.get("mobile")
    if not mobile and student:
        mobile = student.phone

    mfa_enabled = bool(hr.get("mfa_enabled"))
    mfa_requirement = "required" if mfa_enabled else str(hr.get("mfa_requirement") or "optional")

    form = EditUserInformationFormValues(
        full_name=user.full_name,
        display_name=hr.get("display_name") or user.full_name,
        official_email=user.email,
        personal_email=hr.get("personal_email"),
        mobile_number=mobile,
        alternate_phone=hr.get("alternate_phone"),
        department_id=str(user.department_id) if user.department_id else None,
        designation=employee.designation if employee else None,
        username=_username_from_email(user.email),
        login_method=str(hr.get("login_method") or "sso_google"),
        mfa_requirement=mfa_requirement,
        session_timeout_minutes=int(hr.get("session_timeout_minutes") or default_session),
    )

    modified_history = await (
        InstitutionAccessHistory.find(
            Eq(InstitutionAccessHistory.tenant_id, tenant_id),
            Eq(InstitutionAccessHistory.user_id, user_id),
        )
        .sort("-created_at")
        .limit(1)
        .to_list()
    )
    modified_by = "—"
    modified_at = institution.updated_at or user.updated_at
    if modified_history:
        actor = await User.get(modified_history[0].actor_id) if modified_history[0].actor_id else None
        if actor:
            modified_by = actor.full_name
        modified_at = modified_history[0].created_at

    user_id_str = str(user_id)
    account_status = EditUserAccountStatusCard(
        status_label=status_label,
        status_tone=status_tone,
        created_label=_format_ist_date(user.created_at),
        last_modified_label=f"{_format_ist_date(modified_at)} by {modified_by}",
    )

    danger_actions = [
        EditUserDangerAction(
            key="suspend",
            title="Suspend account",
            description="Blocks login; data is kept",
            href=f"/college-admin/users/user-account-activation-suspension?userId={user_id_str}",
            action_label="Suspend",
            icon="ban",
        ),
        EditUserDangerAction(
            key="sign_out",
            title="Force sign-out",
            description="Ends all active sessions",
            href="",
            action_label="Sign out",
            icon="lock",
            api_action="revoke_sessions",
        ),
    ]

    return EditUserInformationPageRead(
        page_title="Edit User Information",
        page_subtitle=f"Update profile details for {user.full_name} ({public_id})",
        detail_href=f"/college-admin/users/user-details?userId={user_id_str}",
        discard_label="Discard",
        save_label="Save changes",
        cancel_label="Cancel",
        profile_section_title="Profile",
        login_section_title="Login & security",
        account_status_section_title="Account status",
        danger_zone_title="Danger zone",
        profile_field_meta=_PROFILE_FIELD_META,
        login_field_meta=_LOGIN_FIELD_META,
        department_options=dept_options,
        designation_options=designation_options,
        login_method_options=_LOGIN_METHOD_OPTIONS,
        mfa_options=_MFA_OPTIONS,
        session_timeout_options=_session_timeout_options(default_session),
        account_status=account_status,
        danger_actions=danger_actions,
        form=form,
        audit_footer_note="Changes are saved to the audit log with your name and time.",
        footer_disclaimer="Live institution user records · Profile from stored accounts · All times IST",
        footer_snapshot_label="Live snapshot",
        user_id=user_id_str,
        generated_at=utcnow(),
    )


async def save_edit_user_information(
    scope: AccessScope,
    payload: EditUserInformationSavePayload,
) -> EditUserInformationPageRead:
    authorize(scope, Permission.INSTITUTION_USER_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    user_id = to_object_id(payload.user_id, "user id")
    user, institution, employee, student, _, _, _ = await _load_user_context(scope, user_id)
    form = _coerce_edit_form(payload.values)

    if not form.full_name or not form.official_email:
        raise AppError(code="VALIDATION_ERROR", message="Full name and official email are required", status_code=422)

    email = form.official_email.lower()
    if email != user.email.lower():
        existing = await _user_repo.find_by_email_in_tenant(email, tenant_id)
        if existing is not None and existing.id != user.id:
            raise AppError(code="CONFLICT", message="Another user already uses this email", status_code=409)
        user.email = email

    user.full_name = form.full_name
    if form.department_id:
        dept_id = to_object_id(form.department_id, "department_id")
        dept = await Department.get(dept_id)
        if dept is None or dept.tenant_id != tenant_id:
            raise AppError(code="VALIDATION_ERROR", message="Invalid department", status_code=422)
        user.department_id = dept_id
        institution.department_id = dept_id
    user.updated_at = utcnow()
    await user.save()

    institution.updated_at = utcnow()
    await institution.save()

    if employee is None and user.role.value != "student":
        employee = EmployeeRecord(
            tenant_id=tenant_id,
            user_id=user.id,
            department_id=user.department_id,
        )
        await employee.insert()
    if employee:
        if form.designation:
            employee.designation = form.designation
        employee.confidential_hr = {
            **employee.confidential_hr,
            "display_name": form.display_name,
            "personal_email": form.personal_email,
            "mobile": form.mobile_number if form.mobile_number != "—" else None,
            "alternate_phone": form.alternate_phone,
            "login_method": form.login_method,
            "mfa_requirement": form.mfa_requirement,
            "mfa_enabled": form.mfa_requirement == "required",
            "session_timeout_minutes": form.session_timeout_minutes,
        }
        employee.updated_at = utcnow()
        await employee.save()
    elif student and form.mobile_number and form.mobile_number != "—":
        student.contact_phone = form.mobile_number
        await student.save()

    from app.modules.audit.service import record_audit

    await record_audit(
        actor_id=scope.user_id,
        action="institution.user.profile_updated",
        resource_type="user",
        resource_id=str(user.id),
        tenant_id=tenant_id,
        metadata={"full_name": user.full_name},
    )
    return await get_edit_user_information_page(scope, user_id)


async def get_edit_user_information_page_by_id(scope: AccessScope, user_id_raw: str) -> EditUserInformationPageRead:
    return await get_edit_user_information_page(scope, to_object_id(user_id_raw, "user id"))