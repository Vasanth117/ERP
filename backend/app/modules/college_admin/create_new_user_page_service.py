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
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyRecord
from app.modules.college_admin.student_admin_models import StudentGuardianRelationship
from app.modules.college_admin.identity_models import (
    InstitutionRole,
    InstitutionUserCreateDraft,
    InstitutionUserInvitation,
    InvitationStatus,
)
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
    CreateNewUserProvisioningUploadRead,
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
from app.modules.students.models import ProfileDocumentRef, StudentProfile
from app.modules.lms import storage as file_storage
from fastapi import UploadFile
from app.modules.tenants.models import Department

_WIZARD_STEPS = [
    CreateNewUserWizardStep(key="personal", label="Personal details", step_number=1),
    CreateNewUserWizardStep(key="role_access", label="Role & access", step_number=2),
    CreateNewUserWizardStep(key="review", label="Review & Invite", step_number=3),
]

_SECTIONS = [
    CreateNewUserFormSection(key="personal_details", title="Personal details"),
    CreateNewUserFormSection(key="account_type", title="Account type"),
    CreateNewUserFormSection(key="student_profile", title="Student profile & schooling"),
    CreateNewUserFormSection(key="staff_profile", title="Staff profile"),
    CreateNewUserFormSection(key="documents", title="Photo & documents"),
    CreateNewUserFormSection(key="role_access", title="Role & access"),
]

_STUDENT_EXTENDED_META = [
    InstitutionFieldMeta(key="previous_school", label="Previous school / college"),
    InstitutionFieldMeta(key="programme_code", label="Programme code"),
    InstitutionFieldMeta(key="batch_label", label="Batch / year"),
    InstitutionFieldMeta(key="section_code", label="Section"),
    InstitutionFieldMeta(key="permanent_address", label="Permanent address", field_type="textarea"),
    InstitutionFieldMeta(key="current_address", label="Current address", field_type="textarea"),
    InstitutionFieldMeta(key="guardian_name", label="Guardian name"),
    InstitutionFieldMeta(key="guardian_relationship", label="Guardian relationship", field_type="select"),
    InstitutionFieldMeta(key="guardian_mobile", label="Guardian mobile"),
    InstitutionFieldMeta(key="blood_group", label="Blood group", field_type="select"),
    InstitutionFieldMeta(key="nationality", label="Nationality", field_type="select"),
]

_STAFF_EXTENDED_META = [
    InstitutionFieldMeta(key="specialization", label="Specialization / subject area"),
    InstitutionFieldMeta(key="experience_years", label="Years of experience"),
]

_DOCUMENT_META = [
    InstitutionFieldMeta(key="profile_photo_ref", label="Profile photo", field_type="file"),
    InstitutionFieldMeta(key="identity_document_ref", label="ID / admission document", field_type="file"),
    InstitutionFieldMeta(key="supporting_document_ref", label="Supporting document", field_type="file"),
]

_GUARDIAN_RELATIONSHIP_OPTIONS = [
    InstitutionFieldOption(value="", label="Select relationship"),
    InstitutionFieldOption(value="father", label="Father"),
    InstitutionFieldOption(value="mother", label="Mother"),
    InstitutionFieldOption(value="guardian", label="Guardian"),
    InstitutionFieldOption(value="sibling", label="Sibling"),
    InstitutionFieldOption(value="other", label="Other"),
]

_BLOOD_GROUP_OPTIONS = [
    InstitutionFieldOption(value="", label="Select blood group"),
    *[InstitutionFieldOption(value=g, label=g) for g in ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")],
]

_NATIONALITY_OPTIONS = [
    InstitutionFieldOption(value="", label="Select nationality"),
    InstitutionFieldOption(value="indian", label="Indian"),
    InstitutionFieldOption(value="other", label="Other"),
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
        initial_password=str(raw.get("initial_password") or ""),
        send_invitation_email=bool(raw.get("send_invitation_email", False)),
        send_sms_login_link=bool(raw.get("send_sms_login_link", False)),
        require_mfa_first_login=bool(raw.get("require_mfa_first_login", True)),
        allow_sso_login=bool(raw.get("allow_sso_login", True)),
        previous_school=str(raw.get("previous_school") or "").strip(),
        programme_code=str(raw.get("programme_code") or "").strip(),
        batch_label=str(raw.get("batch_label") or "").strip(),
        section_code=str(raw.get("section_code") or "").strip(),
        permanent_address=str(raw.get("permanent_address") or "").strip(),
        current_address=str(raw.get("current_address") or "").strip(),
        guardian_name=str(raw.get("guardian_name") or "").strip(),
        guardian_relationship=str(raw.get("guardian_relationship") or "").strip(),
        guardian_mobile=str(raw.get("guardian_mobile") or "").strip(),
        blood_group=raw.get("blood_group") or None,
        nationality=raw.get("nationality") or None,
        specialization=str(raw.get("specialization") or "").strip(),
        experience_years=str(raw.get("experience_years") or "").strip(),
        profile_photo_ref=raw.get("profile_photo_ref") or None,
        identity_document_ref=raw.get("identity_document_ref") or None,
        supporting_document_ref=raw.get("supporting_document_ref") or None,
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
            conflict_invite = await InstitutionUserInvitation.find_one(
                Eq(InstitutionUserInvitation.tenant_id, tenant_id),
                Eq(InstitutionUserInvitation.status, InvitationStatus.PENDING),
                Eq(InstitutionUserInvitation.provisioning_reference_id, public_id),
            )
            if conflict_user or conflict_invite:
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

    if form.send_invitation_email:
        checks.append(
            CreateNewUserValidationCheck(
                key="login_method",
                title="Login method",
                subtitle="User sets password when they accept the invitation",
                status_code="valid",
                status_label="Invitation",
                tone="muted",
            ),
        )
    else:
        password = form.initial_password
        if len(password) < 8:
            pwd_code, pwd_label, pwd_tone = "invalid", "Too short", "error"
            pwd_sub = "Minimum 8 characters"
        else:
            pwd_code, pwd_label, pwd_tone = "valid", "Ready", "success"
            pwd_sub = "Admin-set password for first login"
        checks.append(
            CreateNewUserValidationCheck(
                key="initial_password",
                title="Login password",
                subtitle=pwd_sub,
                status_code=pwd_code,
                status_label=pwd_label,
                tone=pwd_tone,
            ),
        )
    return checks


def _provisioning_extras_from_form(form: CreateNewUserFormValues) -> dict[str, Any]:
    return {
        "user_type": form.user_type,
        "mobile_number": form.mobile_number,
        "previous_school": form.previous_school,
        "programme_code": form.programme_code,
        "batch_label": form.batch_label,
        "section_code": form.section_code,
        "permanent_address": form.permanent_address,
        "current_address": form.current_address,
        "guardian_name": form.guardian_name,
        "guardian_relationship": form.guardian_relationship,
        "guardian_mobile": form.guardian_mobile,
        "blood_group": form.blood_group,
        "nationality": form.nationality,
        "specialization": form.specialization,
        "experience_years": form.experience_years,
        "profile_photo_ref": form.profile_photo_ref,
        "identity_document_ref": form.identity_document_ref,
        "supporting_document_ref": form.supporting_document_ref,
        "designation": form.designation,
        "require_mfa_first_login": form.require_mfa_first_login,
    }


def _document_refs_from_extras(extras: dict[str, Any]) -> list[ProfileDocumentRef]:
    refs: list[ProfileDocumentRef] = []
    if extras.get("identity_document_ref"):
        refs.append(
            ProfileDocumentRef(
                label="Identity document",
                file_id=str(extras["identity_document_ref"]),
                document_type="identity",
            ),
        )
    if extras.get("supporting_document_ref"):
        refs.append(
            ProfileDocumentRef(
                label="Supporting document",
                file_id=str(extras["supporting_document_ref"]),
                document_type="supporting",
            ),
        )
    return refs


async def apply_user_provisioning(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    role: Role,
    form: CreateNewUserFormValues,
    *,
    department_id: PydanticObjectId | None,
    campus_id: PydanticObjectId | None,
) -> None:
    extras = _provisioning_extras_from_form(form)
    dept_oid = department_id

    if role == Role.STUDENT:
        profile = await StudentProfile.find_one(
            Eq(StudentProfile.tenant_id, tenant_id),
            Eq(StudentProfile.user_id, user_id),
        )
        docs = _document_refs_from_extras(extras)
        if profile is None:
            profile = StudentProfile(
                tenant_id=tenant_id,
                user_id=user_id,
                roll_number=form.public_id or None,
                student_id=form.public_id or None,
                department_id=dept_oid,
                programme_code=form.programme_code or None,
                batch_label=form.batch_label or None,
                section_code=form.section_code or None,
                contact_phone=form.mobile_number or None,
                permanent_address=form.permanent_address or None,
                current_address=form.current_address or None,
                profile_photo_ref=form.profile_photo_ref,
                document_refs=docs,
            )
            await profile.insert()
        else:
            if form.public_id:
                profile.roll_number = form.public_id
                profile.student_id = form.public_id
            profile.department_id = dept_oid or profile.department_id
            profile.programme_code = form.programme_code or profile.programme_code
            profile.batch_label = form.batch_label or profile.batch_label
            profile.section_code = form.section_code or profile.section_code
            profile.contact_phone = form.mobile_number or profile.contact_phone
            profile.permanent_address = form.permanent_address or profile.permanent_address
            profile.current_address = form.current_address or profile.current_address
            if form.profile_photo_ref:
                profile.profile_photo_ref = form.profile_photo_ref
            if docs:
                profile.document_refs = docs
            profile.updated_at = utcnow()
            await profile.save()

        if form.guardian_name and form.guardian_mobile:
            guardian = await StudentGuardianRelationship.find_one(
                Eq(StudentGuardianRelationship.tenant_id, tenant_id),
                Eq(StudentGuardianRelationship.user_id, user_id),
            )
            relationship = form.guardian_relationship or "guardian"
            if guardian is None:
                await StudentGuardianRelationship(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    guardian_name=form.guardian_name,
                    relationship=relationship,
                    phone=form.guardian_mobile,
                ).insert()
            else:
                guardian.guardian_name = form.guardian_name
                guardian.relationship = relationship
                guardian.phone = form.guardian_mobile
                guardian.updated_at = utcnow()
                await guardian.save()
        return

    user_oid = user_id
    emp = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, user_oid))
    if emp is None and form.public_id:
        emp = await EmployeeRecord.find_one(
            Eq(EmployeeRecord.tenant_id, tenant_id),
            Eq(EmployeeRecord.employee_id, form.public_id),
        )
    if emp is None:
        await EmployeeRecord(
            tenant_id=tenant_id,
            user_id=user_oid,
            employee_id=form.public_id or None,
            designation=form.designation,
            department_id=dept_oid,
            campus_id=campus_id,
            is_faculty=form.user_type == "teaching_staff",
            joining_date=form.joining_date,
            confidential_hr={
                "mfa_enabled": form.require_mfa_first_login,
                "mobile": form.mobile_number,
                "previous_school": form.previous_school,
            },
        ).insert()
    else:
        emp.user_id = user_oid
        if form.designation:
            emp.designation = form.designation
        emp.department_id = dept_oid or emp.department_id
        emp.joining_date = form.joining_date or emp.joining_date
        emp.confidential_hr = {
            **emp.confidential_hr,
            "mfa_enabled": form.require_mfa_first_login,
            "mobile": form.mobile_number or emp.confidential_hr.get("mobile"),
        }
        await emp.save()

    if form.user_type == "teaching_staff" and (form.specialization or form.experience_years):
        years: float | None = None
        if form.experience_years:
            try:
                years = float(form.experience_years)
            except ValueError:
                years = None
        faculty = await FacultyRecord.find_one(Eq(FacultyRecord.tenant_id, tenant_id), Eq(FacultyRecord.user_id, user_oid))
        if faculty is None:
            await FacultyRecord(
                tenant_id=tenant_id,
                user_id=user_oid,
                department_id=dept_oid,
                campus_id=campus_id,
                designation=form.designation,
                specialization=form.specialization or None,
                experience_years=years,
            ).insert()
        else:
            faculty.specialization = form.specialization or faculty.specialization
            faculty.experience_years = years if years is not None else faculty.experience_years
            faculty.updated_at = utcnow()
            await faculty.save()


async def upload_create_new_user_file(
    scope: AccessScope,
    kind: str,
    upload: UploadFile,
) -> CreateNewUserProvisioningUploadRead:
    authorize(scope, Permission.INSTITUTION_USER_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    allowed = {"profile_photo", "identity_document", "supporting_document"}
    if kind not in allowed:
        raise AppError(code="VALIDATION_ERROR", message="Unknown upload type", status_code=422)

    raw = await upload.read()
    mime = upload.content_type or "application/octet-stream"
    file_storage.validate_upload(upload.filename or "upload.bin", mime, len(raw))
    storage_key = file_storage.storage_key_for(str(tenant_id), "user_provisioning", upload.filename or "upload.bin")
    file_storage.write_bytes(storage_key, raw)
    return CreateNewUserProvisioningUploadRead(
        file_id=storage_key,
        file_name=upload.filename or "upload.bin",
        kind=kind,
    )


def _build_review_lines(form: CreateNewUserFormValues, dept_name: str | None, role_name: str | None) -> list[CreateNewUserReviewLine]:
    full_name = f"{form.first_name} {form.last_name}".strip()
    user_type = next((o.label for o in _USER_TYPE_OPTIONS if o.value == form.user_type), form.user_type)
    lines = [
        CreateNewUserReviewLine(label="Name", value=full_name or "—"),
        CreateNewUserReviewLine(label="Email", value=form.official_email or "—"),
        CreateNewUserReviewLine(label="User type", value=user_type),
        CreateNewUserReviewLine(label="Department", value=dept_name or "—"),
        CreateNewUserReviewLine(label="Designation", value=form.designation or "—"),
        CreateNewUserReviewLine(label="ID", value=form.public_id or "—"),
        CreateNewUserReviewLine(
            label="Login",
            value="Email invitation" if form.send_invitation_email else "Admin-set password",
        ),
        CreateNewUserReviewLine(label="Institution role", value=role_name or "Default role only"),
    ]
    if form.user_type == "student":
        if form.previous_school:
            lines.append(CreateNewUserReviewLine(label="Previous school", value=form.previous_school))
        if form.guardian_name:
            lines.append(CreateNewUserReviewLine(label="Guardian", value=form.guardian_name))
    elif form.specialization:
        lines.append(CreateNewUserReviewLine(label="Specialization", value=form.specialization))
    if form.profile_photo_ref:
        lines.append(CreateNewUserReviewLine(label="Profile photo", value="Uploaded"))
    return lines


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
        page_subtitle="Create student, faculty or staff accounts with admin-set login and full profile details",
        cancel_href="/college-admin/users/user-management-dashboard",
        cancel_label="Cancel",
        create_invite_label="Create account & send invite"
        if form.send_invitation_email
        else "Create account",
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
        student_field_meta=_STUDENT_EXTENDED_META,
        staff_field_meta=_STAFF_EXTENDED_META,
        document_field_meta=_DOCUMENT_META,
        guardian_relationship_options=_GUARDIAN_RELATIONSHIP_OPTIONS,
        blood_group_options=_BLOOD_GROUP_OPTIONS,
        nationality_options=_NATIONALITY_OPTIONS,
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
    allowed = (
        {m.key for m in _PERSONAL_FIELD_META}
        | {m.key for m in _STUDENT_EXTENDED_META}
        | {m.key for m in _STAFF_EXTENDED_META}
        | {m.key for m in _DOCUMENT_META}
        | {
            "initial_password",
            "send_invitation_email",
            "send_sms_login_link",
            "require_mfa_first_login",
            "allow_sso_login",
        }
    )
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

    from app.modules.college_admin.form_validation_details import raise_validation_error, scroll_field

    missing_user: list[dict] = []
    if not form.first_name:
        missing_user.append(scroll_field("first_name", label="First name", message="Enter the user's first name."))
    if not form.last_name:
        missing_user.append(scroll_field("last_name", label="Last name", message="Enter the user's last name."))
    if not form.official_email:
        missing_user.append(
            scroll_field("official_email", label="Official email", message="Enter the user's official email.")
        )
    if missing_user:
        raise_validation_error("Name and email are required.", missing_user)

    validation = await validate_create_new_user(scope, payload.values)
    blocking = [c for c in validation.validation_checks if c.status_code == "invalid"]
    if blocking:
        raise AppError(
            code="VALIDATION_ERROR",
            message=blocking[0].title,
            status_code=422,
            details=[
                scroll_field(c.key, label=c.title, message=c.subtitle or c.title)
                for c in blocking
            ],
        )

    full_name = f"{form.first_name} {form.last_name}".strip()
    role = _role_for_user_type(form.user_type)
    department_id = form.department_id
    campus_id = form.campus_id

    detail_href: str | None = None
    user_id: str | None = None
    invitation_id: str | None = None
    accept_token: str | None = None

    dept_oid = to_object_id(department_id, "department_id") if department_id else None
    campus_oid = to_object_id(campus_id, "campus_id") if campus_id else None

    if form.send_invitation_email:
        extras = _provisioning_extras_from_form(form)
        invite = await invite_institution_user(
            scope,
            InstitutionUserInvite(
                email=form.official_email,
                full_name=full_name,
                role=role,
                department_id=department_id,
                campus_id=campus_id,
                institution_role_id=form.institution_role_id,
                provisioning_reference_id=form.public_id or None,
            ),
        )
        from app.modules.college_admin.identity_models import InstitutionUserInvitation

        invitation_doc = await InstitutionUserInvitation.get(to_object_id(invite.invitation_id, "invitation"))
        if invitation_doc is not None:
            invitation_doc.provisioning_extras = extras
            await invitation_doc.save()
        invitation_id = invite.invitation_id
        accept_token = invite.accept_token
        message = f"Invitation sent to {form.official_email}"
    else:
        if len(form.initial_password) < 8:
            raise_validation_error(
                "Set a secure initial password.",
                [
                    scroll_field(
                        "initial_password",
                        label="Initial password",
                        message="Password must be at least 8 characters.",
                    )
                ],
            )
        created = await create_institution_user(
            scope,
            InstitutionUserCreate(
                email=form.official_email,
                password=form.initial_password,
                full_name=full_name,
                role=role,
                department_id=department_id,
                campus_id=campus_id,
            ),
        )
        user_id = created.user_id
        detail_href = f"/college-admin/users/user-details?userId={user_id}"
        message = f"User {full_name} created — they can sign in with the email and password you set"

    if user_id and form.institution_role_id and not form.send_invitation_email:
        from app.modules.college_admin.user_management_service import assign_user_roles

        await assign_user_roles(
            scope,
            to_object_id(user_id, "user id"),
            UserRoleAssign(institution_role_id=form.institution_role_id),
        )

    if user_id:
        await apply_user_provisioning(
            tenant_id,
            to_object_id(user_id, "user id"),
            role,
            form,
            department_id=dept_oid,
            campus_id=campus_oid,
        )

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