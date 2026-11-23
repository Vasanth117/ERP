"""Add new faculty / employee wizard (CA 07.05)."""

from __future__ import annotations

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
from app.core.exceptions import AppError
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import (
    EmployeeRecord,
    FacultyDepartmentAssignment,
    FacultyEmploymentStatus,
    FacultyNewHireDraft,
    FacultyRecord,
)
from app.modules.college_admin.faculty_admin_schemas import FacultyRecordCreate
from app.modules.college_admin.faculty_admin_service import create_faculty_record
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AddNewFacultyEmployeeAccessCard,
    AddNewFacultyEmployeeCreatePayload,
    AddNewFacultyEmployeeCreateResult,
    AddNewFacultyEmployeeDraftUpdate,
    AddNewFacultyEmployeeFormValues,
    AddNewFacultyEmployeeIdCard,
    AddNewFacultyEmployeePageRead,
    AddNewFacultyEmployeeWizardStep,
    InstitutionFieldMeta,
    InstitutionFieldOption,
)
from app.modules.faculty.models import QualificationRecord
from app.repositories.user_repository import UserRepository

_USER_REPO = UserRepository()

_WIZARD_STEPS: list[tuple[str, str]] = [
    ("personal", "Personal"),
    ("employment", "Employment"),
    ("qualifications", "Qualifications"),
    ("documents", "Documents"),
    ("account", "Account"),
]

_DEFAULT_DESIGNATIONS = [
    "Professor",
    "Associate Professor",
    "Assistant Professor",
    "Lecturer",
    "HOD",
    "Lab Instructor",
    "Administrative Officer",
    "Accounts Executive",
]

_EMPLOYMENT_FIELD_META = [
    InstitutionFieldMeta(key="employee_type", label="Employee type", required=True),
    InstitutionFieldMeta(key="department_id", label="Department", required=True),
    InstitutionFieldMeta(key="designation", label="Designation", required=True),
    InstitutionFieldMeta(key="joining_date", label="Joining date", required=True, field_type="date"),
    InstitutionFieldMeta(key="reporting_to", label="Reporting to"),
    InstitutionFieldMeta(key="employment_status", label="Employment status", required=True),
    InstitutionFieldMeta(key="contract_end_date", label="Contract end date", field_type="date"),
    InstitutionFieldMeta(key="official_email", label="Official email", required=True, field_type="email"),
]

_PERSONAL_FIELD_META = [
    InstitutionFieldMeta(key="full_name", label="Full name", required=True),
    InstitutionFieldMeta(key="mobile", label="Mobile", required=True),
    InstitutionFieldMeta(key="date_of_birth", label="Date of birth", field_type="date"),
    InstitutionFieldMeta(key="gender", label="Gender"),
    InstitutionFieldMeta(key="residential_address", label="Address", field_type="textarea"),
]

_QUALIFICATION_FIELD_META = [
    InstitutionFieldMeta(key="degree", label="Highest qualification", required=True),
    InstitutionFieldMeta(key="institution", label="Institution"),
    InstitutionFieldMeta(key="qualification_year", label="Year"),
    InstitutionFieldMeta(key="specialization", label="Specialization"),
    InstitutionFieldMeta(key="experience_years", label="Experience (years)"),
]

_ACCOUNT_FIELD_META = [
    InstitutionFieldMeta(key="password", label="Temporary password", required=True, field_type="password"),
    InstitutionFieldMeta(key="confirm_password", label="Confirm password", required=True, field_type="password"),
]

_GENDER_OPTIONS = [
    InstitutionFieldOption(value="", label="Select"),
    InstitutionFieldOption(value="male", label="Male"),
    InstitutionFieldOption(value="female", label="Female"),
    InstitutionFieldOption(value="other", label="Other"),
]

_DOCUMENT_CHECKLIST = [
    InstitutionFieldOption(value="ids_verified", label="Government ID verified"),
    InstitutionFieldOption(value="degree_certificates", label="Degree certificates"),
    InstitutionFieldOption(value="experience", label="Experience / relieving letters"),
]


def _parse_date(raw: str | None) -> date | None:
    if not raw or not str(raw).strip():
        return None
    try:
        return date.fromisoformat(str(raw).strip()[:10])
    except ValueError:
        return None


def _coerce_form(raw: dict[str, Any]) -> AddNewFacultyEmployeeFormValues:
    return AddNewFacultyEmployeeFormValues(**{**AddNewFacultyEmployeeFormValues().model_dump(), **raw})


async def _next_employee_id(tenant_id: PydanticObjectId) -> str:
    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    max_num = 3000
    for row in employees:
        eid = row.employee_id or ""
        if not eid.upper().startswith("EMP-"):
            continue
        suffix = eid.split("-", 1)[-1]
        if suffix.isdigit():
            max_num = max(max_num, int(suffix))
    return f"EMP-{max_num + 1:04d}"


async def _get_or_create_draft(tenant_id: PydanticObjectId, actor_id: PydanticObjectId) -> FacultyNewHireDraft:
    existing = await FacultyNewHireDraft.find_one(
        Eq(FacultyNewHireDraft.tenant_id, tenant_id),
        Eq(FacultyNewHireDraft.created_by, actor_id),
    )
    if existing:
        return existing
    draft = FacultyNewHireDraft(tenant_id=tenant_id, created_by=actor_id)
    await draft.insert()
    return draft


def _wizard_steps(current_key: str) -> list[AddNewFacultyEmployeeWizardStep]:
    keys = [k for k, _ in _WIZARD_STEPS]
    try:
        current_index = keys.index(current_key)
    except ValueError:
        current_index = 0
    steps: list[AddNewFacultyEmployeeWizardStep] = []
    for index, (key, label) in enumerate(_WIZARD_STEPS):
        if index < current_index:
            status = "done"
        elif key == current_key:
            status = "active"
        else:
            status = "pending"
        steps.append(
            AddNewFacultyEmployeeWizardStep(
                key=key,
                label=label,
                step_number=index + 1,
                status=status,
            )
        )
    return steps


def _field_meta_for_step(step_key: str) -> list[InstitutionFieldMeta]:
    if step_key == "personal":
        return _PERSONAL_FIELD_META
    if step_key == "employment":
        return _EMPLOYMENT_FIELD_META
    if step_key == "qualifications":
        return _QUALIFICATION_FIELD_META
    if step_key == "account":
        return _ACCOUNT_FIELD_META
    return []


async def _designation_options(tenant_id: PydanticObjectId) -> list[InstitutionFieldOption]:
    faculty = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    values: set[str] = set(_DEFAULT_DESIGNATIONS)
    for row in faculty:
        if row.designation:
            values.add(row.designation.strip())
    for row in employees:
        if row.designation:
            values.add(row.designation.strip())
    opts = [InstitutionFieldOption(value="", label="Select designation")]
    for label in sorted(values, key=str.lower):
        opts.append(InstitutionFieldOption(value=label, label=label))
    return opts


async def _reporting_options(tenant_id: PydanticObjectId) -> list[InstitutionFieldOption]:
    faculty = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    user_by_id: dict[PydanticObjectId, User] = {}
    for record in faculty:
        user = await User.get(record.user_id)
        if user and user.tenant_id == tenant_id:
            user_by_id[record.user_id] = user
    departments = await InstitutionDepartment.find(Eq(InstitutionDepartment.tenant_id, tenant_id)).to_list()
    dept_by_id = {d.id: d for d in departments}

    opts = [InstitutionFieldOption(value="", label="Select reporting manager")]
    for record in faculty:
        designation = (record.designation or "").lower()
        if "hod" not in designation and "head" not in designation:
            continue
        user = user_by_id.get(record.user_id)
        dept = dept_by_id.get(record.department_id) if record.department_id else None
        dept_code = (dept.department_code if dept else "Unit").upper()
        label = f"HOD, {dept_code}"
        opts.append(InstitutionFieldOption(value=label, label=label))
    if len(opts) == 1:
        for record in faculty[:8]:
            user = user_by_id.get(record.user_id)
            if not user:
                continue
            opts.append(InstitutionFieldOption(value=user.full_name, label=user.full_name))
    return opts


async def _page_read(draft: FacultyNewHireDraft) -> AddNewFacultyEmployeePageRead:
    tenant_id = draft.tenant_id
    now = utcnow()
    form = _coerce_form(draft.values)
    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    dept_options = [InstitutionFieldOption(value="", label="Select department")]
    for dept in sorted(departments, key=lambda d: (d.name or "").lower()):
        dept_options.append(InstitutionFieldOption(value=str(dept.id), label=dept.name or dept.department_code))

    if not form.department_id and dept_options:
        form.department_id = dept_options[1].value if len(dept_options) > 1 else ""

    next_id = await _next_employee_id(tenant_id)
    role_label = "Faculty" if (form.employee_type or "faculty") == "faculty" else "Staff"

    employment_status_options = [
        InstitutionFieldOption(value=FacultyEmploymentStatus.PROBATION.value, label="Probation"),
        InstitutionFieldOption(value=FacultyEmploymentStatus.ACTIVE.value, label="Active"),
        InstitutionFieldOption(value=FacultyEmploymentStatus.CONFIRMED.value, label="Confirmed"),
        InstitutionFieldOption(value=FacultyEmploymentStatus.AWAITING_CONFIRMATION.value, label="Awaiting confirmation"),
    ]

    return AddNewFacultyEmployeePageRead(
        draft_id=str(draft.id),
        page_title="Add New Faculty / Employee",
        page_subtitle="Create a staff record and login",
        back_href="/college-admin/faculty/employee-directory",
        back_label="Back",
        save_draft_label="Save draft",
        create_label="Create",
        current_step_key=draft.step_key,
        steps=_wizard_steps(draft.step_key),
        employment_section_title="Employment details",
        field_meta=_PERSONAL_FIELD_META
        + _EMPLOYMENT_FIELD_META
        + _QUALIFICATION_FIELD_META
        + _ACCOUNT_FIELD_META,
        form=form,
        employee_type_options=[
            InstitutionFieldOption(value="faculty", label="Faculty"),
            InstitutionFieldOption(value="staff", label="Staff"),
            InstitutionFieldOption(value="contract", label="Contract"),
        ],
        department_options=dept_options,
        designation_options=await _designation_options(tenant_id),
        employment_status_options=employment_status_options,
        reporting_to_options=await _reporting_options(tenant_id),
        gender_options=_GENDER_OPTIONS,
        document_checklist=_DOCUMENT_CHECKLIST,
        access_card=AddNewFacultyEmployeeAccessCard(
            role_label=role_label,
            login_created_label="After approval",
        ),
        employee_id_card=AddNewFacultyEmployeeIdCard(next_id_value=next_id),
        has_draft=bool(draft.values),
        footer_disclaimer="Live institutional data · Faculty and employee records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def get_add_new_faculty_employee_page(scope: AccessScope) -> AddNewFacultyEmployeePageRead:
    authorize(scope, Permission.FACULTY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    actor_id = scope.user_id
    assert actor_id is not None
    draft = await _get_or_create_draft(tenant_id, actor_id)
    if not draft.values:
        next_id = await _next_employee_id(tenant_id)
        draft.values = {"employee_type": "faculty", "employment_status": FacultyEmploymentStatus.PROBATION.value}
        draft.values["employee_id_reserved"] = next_id
        await draft.save()
    return await _page_read(draft)


async def save_add_new_faculty_employee_draft(
    scope: AccessScope,
    payload: AddNewFacultyEmployeeDraftUpdate,
) -> AddNewFacultyEmployeePageRead:
    authorize(scope, Permission.FACULTY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    actor_id = scope.user_id
    assert actor_id is not None

    if payload.draft_id:
        draft_oid = to_object_id(payload.draft_id, "draft_id")
        draft = await FacultyNewHireDraft.get(draft_oid)
        if draft is None or draft.tenant_id != tenant_id or draft.created_by != actor_id:
            raise AppError(code="NOT_FOUND", message="Draft not found", status_code=404)
    else:
        draft = await _get_or_create_draft(tenant_id, actor_id)

    merged = {**draft.values, **(payload.values or {})}
    draft.values = merged
    if payload.step_key:
        draft.step_key = payload.step_key
    draft.updated_at = utcnow()
    await draft.save()
    return await _page_read(draft)


def _validate_create(form: AddNewFacultyEmployeeFormValues) -> None:
    from app.modules.college_admin.form_validation_details import (
        navigate_field,
        raise_validation_error,
        scroll_field,
    )

    details: list[dict] = []
    if not form.full_name.strip():
        details.append(scroll_field("full_name", label="Full name", message="Enter the employee's full name."))
    if not form.official_email.strip():
        details.append(
            scroll_field("official_email", label="Official email", message="Enter the institutional email address.")
        )
    if not form.department_id:
        details.append(
            navigate_field(
                "department_id",
                label="Department",
                message="Select the department this employee belongs to, or create a department first.",
                action_label="Create department",
                action_href="/college-admin/organization/create-department",
            )
        )
    if not form.designation:
        details.append(scroll_field("designation", label="Designation", message="Select or enter the designation."))
    if not form.joining_date:
        details.append(scroll_field("joining_date", label="Joining date", message="Enter the date of joining."))
    if not form.password or len(form.password) < 8:
        details.append(
            scroll_field("password", label="Password", message="Password must be at least 8 characters.")
        )
    if form.password != form.confirm_password:
        details.append(
            scroll_field("confirm_password", label="Confirm password", message="Passwords must match.")
        )
    if details:
        raise_validation_error("Complete the required fields before creating the employee.", details)


async def create_add_new_faculty_employee(
    scope: AccessScope,
    payload: AddNewFacultyEmployeeCreatePayload,
) -> AddNewFacultyEmployeeCreateResult:
    authorize(scope, Permission.FACULTY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    actor_id = scope.user_id
    assert actor_id is not None

    draft_oid = to_object_id(payload.draft_id, "draft_id")
    draft = await FacultyNewHireDraft.get(draft_oid)
    if draft is None or draft.tenant_id != tenant_id or draft.created_by != actor_id:
        raise AppError(code="NOT_FOUND", message="Draft not found", status_code=404)

    merged = {**draft.values, **(payload.values or {})}
    form = _coerce_form(merged)
    _validate_create(form)

    employee_id = str(merged.get("employee_id_reserved") or await _next_employee_id(tenant_id))
    joining_date = _parse_date(form.joining_date)
    status = FacultyEmploymentStatus(form.employment_status) if form.employment_status else FacultyEmploymentStatus.PROBATION
    employment_type = (form.employee_type or "faculty").strip().lower()
    is_faculty = employment_type == "faculty"

    if is_faculty:
        qualifications: list[QualificationRecord] = []
        if form.degree:
            year = int(form.qualification_year) if (form.qualification_year or "").isdigit() else None
            qualifications.append(
                QualificationRecord(degree=form.degree, institution=form.institution or None, year=year)
            )
        create_payload = FacultyRecordCreate(
            email=form.official_email.strip().lower(),
            password=form.password,
            full_name=form.full_name.strip(),
            employee_id=employee_id,
            designation=form.designation,
            department_id=form.department_id or None,
            specialization=form.specialization or None,
            employment_type=employment_type,
            joining_date=joining_date,
        )
        created = await create_faculty_record(scope, create_payload)
        record = await FacultyRecord.get(to_object_id(created.record_id, "record_id"))
        if record:
            record.employment_status = status
            if qualifications:
                record.qualifications = qualifications
            if form.experience_years:
                try:
                    record.experience_years = float(form.experience_years)
                except ValueError:
                    pass
            await record.save()
            employee = await EmployeeRecord.find_one(
                Eq(EmployeeRecord.tenant_id, tenant_id),
                Eq(EmployeeRecord.user_id, record.user_id),
            )
            if employee:
                employee.employment_status = status
                if form.mobile:
                    employee.confidential_hr = {**employee.confidential_hr, "mobile": form.mobile}
                if form.residential_address:
                    employee.confidential_hr = {**employee.confidential_hr, "address": form.residential_address}
                if form.reporting_to:
                    employee.confidential_hr = {**employee.confidential_hr, "reporting_to": form.reporting_to}
                contract_end = _parse_date(form.contract_end_date)
                if contract_end:
                    employee.confidential_hr = {**employee.confidential_hr, "contract_end_date": contract_end.isoformat()}
                await employee.save()
        await draft.delete()
        return AddNewFacultyEmployeeCreateResult(
            record_id=created.record_id,
            employee_id=employee_id,
            detail_href=f"/college-admin/faculty/faculty-profile?id={created.record_id}",
        )

    email = form.official_email.strip().lower()
    if await _USER_REPO.find_by_email_in_tenant(email, tenant_id):
        raise AppError(code="CONFLICT", message="Email already exists", status_code=409)
    if await EmployeeRecord.find_one(
        Eq(EmployeeRecord.tenant_id, tenant_id),
        Eq(EmployeeRecord.employee_id, employee_id),
    ):
        raise AppError(code="CONFLICT", message="Employee identifier already assigned", status_code=409)

    dept_id = to_object_id(form.department_id, "department_id") if form.department_id else None
    user = User(
        email=email,
        hashed_password=hash_password(form.password),
        full_name=form.full_name.strip(),
        role=Role.HR_STAFF,
        tenant_id=tenant_id,
        department_id=dept_id,
    )
    await user.insert()

    employee = EmployeeRecord(
        tenant_id=tenant_id,
        user_id=user.id,
        employee_id=employee_id,
        employment_type=employment_type,
        joining_date=joining_date,
        designation=form.designation,
        department_id=dept_id,
        employment_status=status,
        is_faculty=False,
        confidential_hr={
            "mobile": form.mobile,
            "address": form.residential_address,
            "emergency_contact": "",
            "reporting_to": form.reporting_to,
        },
        updated_by=actor_id,
    )
    if form.contract_end_date:
        contract_end = _parse_date(form.contract_end_date)
        if contract_end:
            employee.confidential_hr["contract_end_date"] = contract_end.isoformat()
    await employee.insert()

    await draft.delete()
    return AddNewFacultyEmployeeCreateResult(
        record_id=str(employee.id),
        employee_id=employee_id,
        detail_href=f"/college-admin/faculty/employee-profile-management?id={employee.id}",
    )