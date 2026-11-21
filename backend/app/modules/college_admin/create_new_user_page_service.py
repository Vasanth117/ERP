"""Create new user wizard (CA 03 — create & invite)."""

from __future__ import annotations

import re
import secrets
from datetime import date
from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.roles import Role
from app.common.time import utcnow
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.college_admin.identity_models import InstitutionRole, InstitutionUserCreateDraft
from app.modules.college_admin.models import InstitutionCampus, InstitutionProfile
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.role_management_service import list_institution_roles
from app.modules.college_admin.schemas import (
    CreateNewUserDraftUpdate,
    CreateNewUserFormSection,
    CreateNewUserFormValues,
    CreateNewUserPageRead,
    CreateNewUserReviewLine,
    CreateNewUserSubmitPayload,
    CreateNewUserSubmitResponse,
    CreateNewUserToggleSetting,
    CreateNewUserValidateResponse,
    CreateNewUserValidationCheck,
    CreateNewUserWizardStep,
    InstitutionFieldMeta,
    InstitutionFieldOption,
)
from app.modules.college_admin.security_admin_models import InstitutionSecurityPolicy
from app.modules.college_admin.user_management_service import create_institution_user, invite_institution_user
from app.modules.college_admin.identity_schemas import (
    InstitutionUserCreate,
    InstitutionUserInvite,
    UserRoleAssign,
)
from app.modules.faculty.models import FacultyProfile
from app.modules.students.models import StudentProfile
from app.modules.tenants.models import Department

_WIZARD_STEPS = [
    CreateNewUserWizardStep(key="personal", label="Personal details", step_number=1),
    CreateNewUserWizardStep(key="role_access", label="Role & access", step_number=2),
    CreateNewUserWizardStep(key="review", label="Review & Invite", step_number=3),
]

_SECTIONS = [
    CreateNewUserFormSection(key="personal_details", title="Personal details"),
    CreateNewUserFormSection(key="account_type", title="Account type"),
    CreateNewUserFormSection(key="role_access", title="Role & access"),
]

_PERSONAL_FIELD_META = [
    InstitutionFieldMeta(key="first_name", label="First name", required=True),
    InstitutionFieldMeta(key="last_name", label="Last name", required=True),
    InstitutionFieldMeta(key="official_email", label="Official email", required=True, field_type="email"),
    InstitutionFieldMeta(key="mobile_number", label="Mobile number", required=True),
    InstitutionFieldMeta(key="public_id", label="Employee / student ID", required=True),
    InstitutionFieldMeta(key="joining_date", label="Date of joining", required=True, field_type="date"),
    InstitutionFieldMeta(key="gender", label="Gender", field_type="select"),
    InstitutionFieldMeta(key="date_of_birth", label="Date of birth", field_type="date"),
    InstitutionFieldMeta(key="user_type", label="User type", required=True, field_type="radio"),
    InstitutionFieldMeta(key="department_id", label="Department", required=True, field_type="select"),
    InstitutionFieldMeta(key="designation", label="Designation", required=True, field_type="select"),
    InstitutionFieldMeta(key="campus_id", label="Campus", field_type="select"),
    InstitutionFieldMeta(key="institution_role_id", label="Institution role", field_type="select"),
]

_USER_TYPE_OPTIONS = [
    InstitutionFieldOption(value="teaching_staff", label="Teaching staff"),
    InstitutionFieldOption(value="non_teaching_staff", label="Non-teaching staff"),
    InstitutionFieldOption(value="student", label="Student"),
]

_GENDER_OPTIONS = [
    InstitutionFieldOption(value="", label="Select gender"),
    InstitutionFieldOption(value="female", label="Female"),
    InstitutionFieldOption(value="male", label="Male"),
    InstitutionFieldOption(value="other", label="Other"),
    InstitutionFieldOption(value="prefer_not_to_say", label="Prefer not to say"),
]

_BASE_DESIGNATIONS = [
    "Professor",
    "Associate Professor",
    "Assistant Professor",
    "Lecturer",
    "Lab Instructor",
    "Administrative Officer",
    "Technical Staff",
    "Office Assistant",
]

_STUDENT_DESIGNATIONS = [InstitutionFieldOption(value="student", label="Student")]


def _role_for_user_type(user_type: str) -> Role:
    if user_type == "student":
        return Role.STUDENT
    if user_type == "non_teaching_staff":
        return Role.HR_STAFF
    return Role.FACULTY


def _coerce_form_values(raw: dict[str, Any]) -> CreateNewUserFormValues:
    joining = raw.get("joining_date")
    dob = raw.get("date_of_birth")
    return CreateNewUserFormValues(
        first_name=str(raw.get("first_name") or "").strip(),
        last_name=str(raw.get("last_name") or "").strip(),
        official_email=str(raw.get("official_email") or "").strip().lower(),
        mobile_number=str(raw.get("mobile_number") or "").strip(),
        public_id=str(raw.get("public_id") or "").strip(),
        joining_date=date.fromisoformat(joining) if isinstance(joining, str) and joining else joining,
        gender=raw.get("gender") or None,
        date_of_birth=date.fromisoformat(dob) if isinstance(dob, str) and dob else dob,
        user_type=str(raw.get("user_type") or "teaching_staff"),
        department_id=raw.get("department_id") or None,
        designation=raw.get("designation") or None,
        campus_id=raw.get("campus_id") or None,
        institution_role_id=raw.get("institution_role_id") or None,
        send_invitation_email=bool(raw.get("send_invitation_email", True)),
        send_sms_login_link=bool(raw.get("send_sms_login_link", False)),
        require_mfa_first_login=bool(raw.get("require_mfa_first_login", True)),
        allow_sso_login=bool(raw.get("allow_sso_login", True)),
    )


async def _get_or_create_draft(tenant_id: PydanticObjectId, actor_id: PydanticObjectId) -> InstitutionUserCreateDraft:
    existing = await InstitutionUserCreateDraft.find_one(
        Eq(InstitutionUserCreateDraft.tenant_id, tenant_id),
        Eq(InstitutionUserCreateDraft.actor_id, actor_id),
    )
    if existing is not None:
        return existing
    draft = InstitutionUserCreateDraft(tenant_id=tenant_id, actor_id=actor_id)
    await draft.insert()
    return draft


def _required_email_domain(profile: InstitutionProfile | None) -> str | None:
    if profile and profile.institution_email and "@" in profile.institution_email:
        return profile.institution_email.split("@", 1)[1].lower()
    return None


async def _build_validation_checks(
    tenant_id: PydanticObjectId,
    form: CreateNewUserFormValues,
    profile: InstitutionProfile | None,
) -> list[CreateNewUserValidationCheck]:
    checks: list[CreateNewUserValidationCheck] = []

    public_id = form.public_id.strip()
    if form.user_type == "student":
        employee_subtitle = "Student roll / admission ID"
        if not public_id:
            emp_status, emp_label, emp_tone = "pending", "Pending", "muted"
        else:
            conflict_user = await StudentProfile.find_one(
                Eq(StudentProfile.tenant_id, tenant_id),
                Eq(StudentProfile.roll_number, public_id),
            )
            if conflict_user:
                emp_status, emp_label, emp_tone = "invalid", "Already used", "error"
            else:
                emp_status, emp_label, emp_tone = "valid", "Ready", "success"
        checks.append(
            CreateNewUserValidationCheck(
                key="public_id",
                title="Student ID must be unique",
                subtitle=employee_subtitle,
                status_code=emp_status,
                status_label=emp_label,
                tone=emp_tone,
            ),
        )
    else:
        if not public_id:
            emp_status, emp_label, emp_tone = "pending", "Pending", "muted"
            hr_note = "Enter employee ID to verify against HR"
        else:
            hr_row = await EmployeeRecord.find_one(
                Eq(EmployeeRecord.tenant_id, tenant_id),
                Eq(EmployeeRecord.employee_id, public_id),
            )
            if hr_row and hr_row.user_id:
                existing = await User.get(hr_row.user_id)
                if existing and existing.tenant_id == tenant_id:
                    emp_status, emp_label, emp_tone = "invalid", "Already linked", "error"
                    hr_note = "Checked against HR Administration"
                else:
                    emp_status, emp_label, emp_tone = "matched", "Matched", "success"
                    hr_note = "Checked against HR Administration"
            elif hr_row:
                emp_status, emp_label, emp_tone = "matched", "Matched", "success"
                hr_note = "Checked against HR Administration"
            elif re.match(r"^[A-Za-z0-9\-]{3,32}$", public_id):
                emp_status, emp_label, emp_tone = "valid", "Ready", "success"
                hr_note = "Ready for new employee record"
            else:
                emp_status, emp_label, emp_tone = "invalid", "Invalid format", "error"
                hr_note = "Use alphanumeric ID (e.g. EMP-1342)"
        checks.append(
            CreateNewUserValidationCheck(
                key="employee_id",
                title="Employee ID must match HR record",
                subtitle=hr_note,
                status_code=emp_status,
                status_label=emp_label,
                tone=emp_tone,
            ),
        )

    domain = _required_email_domain(profile)
    email = form.official_email
    if not domain:
        checks.append(
            CreateNewUserValidationCheck(
                key="email_domain",
                title="Email domain",
                subtitle="Institution domain not configured",
                status_code="valid",
                status_label="Valid",
                tone="success",
            ),
        )
    elif not email or "@" not in email:
        checks.append(
            CreateNewUserValidationCheck(
                key="email_domain",
                title="Email domain",
                subtitle=f"@{domain} required for staff",
                status_code="pending",
                status_label="Pending",
                tone="muted",
            ),
        )
    elif email.split("@", 1)[1].lower() == domain:
        checks.append(
            CreateNewUserValidationCheck(
                key="email_domain",
                title="Email domain",
                subtitle=f"@{domain} required for staff",
                status_code="valid",
                status_label="Valid",
                tone="success",
            ),
        )
    else:
        allowed_student = form.user_type == "student"
        checks.append(
            CreateNewUserValidationCheck(
                key="email_domain",
                title="Email domain",
                subtitle=f"@{domain} required for staff",
                status_code="valid" if allowed_student else "invalid",
                status_label="Valid" if allowed_student else "Invalid",
                tone="success" if allowed_student else "error",
            ),
        )
    return checks


def _build_review_lines(form: CreateNewUserFormValues, dept_name: str | None, role_name: str | None) -> list[CreateNewUserReviewLine]:
    full_name = f"{form.first_name} {form.last_name}".strip()
    user_type = next((o.label for o in _USER_TYPE_OPTIONS if o.value == form.user_type), form.user_type)
    return [
        CreateNewUserReviewLine(label="Name", value=full_name or "—"),
        CreateNewUserReviewLine(label="Email", value=form.official_email or "—"),
        CreateNewUserReviewLine(label="User type", value=user_type),
        CreateNewUserReviewLine(label="Department", value=dept_name or "—"),
        CreateNewUserReviewLine(label="Designation", value=form.designation or "—"),
        CreateNewUserReviewLine(label="ID", value=form.public_id or "—"),
        CreateNewUserReviewLine(
            label="Invitation",
            value="Email invitation" if form.send_invitation_email else "Manual activation",
        ),
        CreateNewUserReviewLine(label="Institution role", value=role_name or "Default role only"),
    ]


async def get_create_new_user_page(scope: AccessScope) -> CreateNewUserPageRead:
    authorize(scope, Permission.INSTITUTION_USER_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    actor_id = scope.user_id
    if actor_id is None:
        raise AppError(code="FORBIDDEN", message="Actor required", status_code=403)

    draft = await _get_or_create_draft(tenant_id, actor_id)
    profile = await InstitutionProfile.find_one(Eq(InstitutionProfile.tenant_id, tenant_id))
    settings = get_settings()
    policy = await InstitutionSecurityPolicy.find_one(
        Eq(InstitutionSecurityPolicy.tenant_id, tenant_id),
        Eq(InstitutionSecurityPolicy.policy_id, "default"),
    )

    departments = await Department.find(Eq(Department.tenant_id, tenant_id)).sort("+name").to_list()
    dept_options = [InstitutionFieldOption(value="", label="Select department")]
    dept_options.extend(InstitutionFieldOption(value=str(d.id), label=d.name) for d in departments)

    campus_rows = await InstitutionCampus.find(Eq(InstitutionCampus.tenant_id, tenant_id)).sort("+name").to_list()
    campus_options = [InstitutionFieldOption(value="", label="Select campus (optional)")]
    campus_options.extend(InstitutionFieldOption(value=str(c.id), label=c.name) for c in campus_rows)

    designations: set[str] = set(_BASE_DESIGNATIONS)
    for row in await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list():
        if row.designation:
            designations.add(row.designation.strip())
    for row in await FacultyProfile.find(Eq(FacultyProfile.tenant_id, tenant_id)).limit(200).to_list():
        if row.designation:
            designations.add(row.designation.strip())
    designation_options = [InstitutionFieldOption(value="", label="Select designation")]
    designation_options.extend(
        InstitutionFieldOption(value=name, label=name) for name in sorted(designations, key=str.lower)
    )

    role_reads = await list_institution_roles(scope)
    institution_role_options = [InstitutionFieldOption(value="", label="Default platform role only")]
    institution_role_options.extend(
        InstitutionFieldOption(value=r.role_id, label=r.name) for r in role_reads if r.name
    )

    merged = {**_coerce_form_values({}).model_dump(mode="json"), **(draft.values or {})}
    form = _coerce_form_values(merged)

    invite_days = max(1, settings.invitation_expire_hours // 24)
    invitation_settings = [
        CreateNewUserToggleSetting(
            key="send_invitation_email",
            label="Send invitation email",
            description=f"Link valid for {invite_days} days",
            default_on=True,
        ),
        CreateNewUserToggleSetting(
            key="send_sms_login_link",
            label="Send SMS with login link",
            description=None,
            default_on=False,
        ),
        CreateNewUserToggleSetting(
            key="require_mfa_first_login",
            label="Require MFA on first login",
            description="Recommended for staff",
            default_on=bool(policy.require_mfa_privileged if policy else True),
        ),
        CreateNewUserToggleSetting(
            key="allow_sso_login",
            label="Allow SSO login",
            description="Google Workspace",
            default_on=True,
        ),
    ]

    validation_checks = await _build_validation_checks(tenant_id, form, profile)
    dept_name = next((d.name for d in departments if str(d.id) == form.department_id), None)
    role_name = next((r.name for r in role_reads if r.role_id == form.institution_role_id), None)
    review_lines = _build_review_lines(form, dept_name, role_name)

    return CreateNewUserPageRead(
        page_title="Create New User",
        page_subtitle="Add a staff or student account and send an invitation",
        cancel_href="/college-admin/users/user-management-dashboard",
        cancel_label="Cancel",
        create_invite_label="Create & send invite",
        save_draft_label="Save as draft",
        next_step_prefix="Next",
        audit_footer_note="Changes are saved to the audit log with your name and time.",
        current_step_key=draft.step_key or "personal",
        steps=_WIZARD_STEPS,
        sections=_SECTIONS,
        field_meta=_PERSONAL_FIELD_META,
        gender_options=_GENDER_OPTIONS,
        user_type_options=_USER_TYPE_OPTIONS,
        department_options=dept_options,
        designation_options=designation_options if form.user_type != "student" else _STUDENT_DESIGNATIONS,
        campus_options=campus_options,
        institution_role_options=institution_role_options,
        invitation_settings=invitation_settings,
        validation_checks=validation_checks,
        review_lines=review_lines,
        form=form,
        has_draft=bool(draft.values),
        footer_disclaimer="Live institution configuration · Options and checks from stored records · All times IST",
        generated_at=utcnow(),
    )


async def save_create_new_user_draft(scope: AccessScope, payload: CreateNewUserDraftUpdate) -> CreateNewUserPageRead:
    authorize(scope, Permission.INSTITUTION_USER_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    actor_id = scope.user_id
    if actor_id is None:
        raise AppError(code="FORBIDDEN", message="Actor required", status_code=403)

    draft = await _get_or_create_draft(tenant_id, actor_id)
    allowed = {m.key for m in _PERSONAL_FIELD_META} | {
        "send_invitation_email",
        "send_sms_login_link",
        "require_mfa_first_login",
        "allow_sso_login",
    }
    draft.values = {**draft.values, **{k: v for k, v in payload.values.items() if k in allowed and v is not None}}
    if payload.step_key:
        draft.step_key = payload.step_key
    draft.updated_at = utcnow()
    await draft.save()
    return await get_create_new_user_page(scope)


async def validate_create_new_user(
    scope: AccessScope,
    values: dict[str, Any],
) -> CreateNewUserValidateResponse:
    authorize(scope, Permission.INSTITUTION_USER_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    profile = await InstitutionProfile.find_one(Eq(InstitutionProfile.tenant_id, tenant_id))
    form = _coerce_form_values(values)
    checks = await _build_validation_checks(tenant_id, form, profile)
    departments = await Department.find(Eq(Department.tenant_id, tenant_id)).to_list()
    dept_name = next((d.name for d in departments if str(d.id) == form.department_id), None)
    role_name = None
    if form.institution_role_id:
        role_doc = await InstitutionRole.get(to_object_id(form.institution_role_id, "institution role"))
        if role_doc and role_doc.tenant_id == tenant_id:
            role_name = role_doc.name
    return CreateNewUserValidateResponse(
        validation_checks=checks,
        review_lines=_build_review_lines(form, dept_name, role_name),
    )


async def submit_create_new_user(
    scope: AccessScope,
    payload: CreateNewUserSubmitPayload,
) -> CreateNewUserSubmitResponse:
    authorize(scope, Permission.INSTITUTION_USER_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    actor_id = scope.user_id
    form = _coerce_form_values(payload.values)

    if not form.first_name or not form.last_name or not form.official_email:
        raise AppError(code="VALIDATION_ERROR", message="Name and email are required", status_code=422)

    validation = await validate_create_new_user(scope, payload.values)
    blocking = [c for c in validation.validation_checks if c.status_code == "invalid"]
    if blocking:
        raise AppError(
            code="VALIDATION_ERROR",
            message=blocking[0].title,
            status_code=422,
            details=[{"field": c.key, "message": c.subtitle} for c in blocking],
        )

    full_name = f"{form.first_name} {form.last_name}".strip()
    role = _role_for_user_type(form.user_type)
    department_id = form.department_id
    campus_id = form.campus_id

    detail_href: str | None = None
    user_id: str | None = None
    invitation_id: str | None = None
    accept_token: str | None = None

    if form.send_invitation_email:
        invite = await invite_institution_user(
            scope,
            InstitutionUserInvite(
                email=form.official_email,
                full_name=full_name,
                role=role,
                department_id=department_id,
                campus_id=campus_id,
                institution_role_id=form.institution_role_id,
            ),
        )
        invitation_id = invite.invitation_id
        accept_token = invite.accept_token
        message = f"Invitation sent to {form.official_email}"
    else:
        temp_password = secrets.token_urlsafe(16)
        created = await create_institution_user(
            scope,
            InstitutionUserCreate(
                email=form.official_email,
                password=temp_password,
                full_name=full_name,
                role=role,
                department_id=department_id,
                campus_id=campus_id,
            ),
        )
        user_id = created.user_id
        detail_href = f"/college-admin/users/user-details?userId={user_id}"
        message = f"User {full_name} created"

    if user_id and form.institution_role_id and not form.send_invitation_email:
        from app.modules.college_admin.user_management_service import assign_user_roles

        await assign_user_roles(
            scope,
            to_object_id(user_id, "user id"),
            UserRoleAssign(institution_role_id=form.institution_role_id),
        )

    # Link or create employee/student identifiers when account exists immediately (non-invite path).
    if user_id and form.user_type != "student" and form.public_id:
        user_oid = to_object_id(user_id, "user id")
        emp = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, user_oid))
        if emp is None:
            emp = await EmployeeRecord.find_one(
                Eq(EmployeeRecord.tenant_id, tenant_id),
                Eq(EmployeeRecord.employee_id, form.public_id),
            )
        dept_oid = to_object_id(department_id, "department_id") if department_id else None
        campus_oid = to_object_id(campus_id, "campus_id") if campus_id else None
        if emp is None:
            await EmployeeRecord(
                tenant_id=tenant_id,
                user_id=user_oid,
                employee_id=form.public_id,
                designation=form.designation,
                department_id=dept_oid,
                campus_id=campus_oid,
                is_faculty=form.user_type == "teaching_staff",
                joining_date=form.joining_date,
                confidential_hr={"mfa_enabled": form.require_mfa_first_login, "mobile": form.mobile_number},
            ).insert()
        else:
            emp.user_id = user_oid
            if form.designation:
                emp.designation = form.designation
            emp.department_id = dept_oid or emp.department_id
            emp.joining_date = form.joining_date or emp.joining_date
            emp.confidential_hr = {**emp.confidential_hr, "mfa_enabled": form.require_mfa_first_login}
            await emp.save()

    if actor_id:
        draft = await InstitutionUserCreateDraft.find_one(
            Eq(InstitutionUserCreateDraft.tenant_id, tenant_id),
            Eq(InstitutionUserCreateDraft.actor_id, actor_id),
        )
        if draft:
            draft.values = {}
            draft.step_key = "personal"
            await draft.save()

    return CreateNewUserSubmitResponse(
        status="ok",
        message=message,
        user_id=user_id,
        invitation_id=invitation_id,
        detail_href=detail_href,
        accept_token=accept_token,
    )