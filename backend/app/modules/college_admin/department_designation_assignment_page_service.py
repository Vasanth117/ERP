"""Department & designation assignment (CA 07.07)."""

from __future__ import annotations

from datetime import date
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import (
    EmployeeRecord,
    FacultyDepartmentAssignment,
    FacultyEmploymentHistory,
    FacultyRecord,
)
from app.modules.college_admin.faculty_admin_service import _sync_employee_snapshot, _sync_faculty_profile
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    DepartmentDesignationApprovalStep,
    DepartmentDesignationAssignmentFormValues,
    DepartmentDesignationAssignmentPageRead,
    DepartmentDesignationAssignmentSavePayload,
    DepartmentDesignationHistoryItem,
    FacultyAssignmentEmployeeOption,
    InstitutionFieldMeta,
    InstitutionFieldOption,
)

_IST = ZoneInfo("Asia/Kolkata")
_DEFAULT_DESIGNATIONS = [
    "Professor",
    "Associate Professor",
    "Assistant Professor",
    "Lecturer",
    "HOD",
    "Lab Instructor",
]

_FIELD_META = [
    InstitutionFieldMeta(key="record_id", label="Employee", required=True),
    InstitutionFieldMeta(key="department_id", label="Department", required=True),
    InstitutionFieldMeta(key="designation", label="Designation", required=True),
    InstitutionFieldMeta(key="reporting_to", label="Reporting to", required=True),
    InstitutionFieldMeta(key="effective_from", label="Effective from", required=True, field_type="date"),
    InstitutionFieldMeta(key="reason", label="Reason", field_type="textarea"),
]


def _parse_date(raw: str | None) -> date | None:
    if not raw or not str(raw).strip():
        return None
    try:
        return date.fromisoformat(str(raw).strip()[:10])
    except ValueError as exc:
        raise AppError(code="VALIDATION_ERROR", message="Invalid effective date", status_code=422) from exc


def _format_date(value: date | None) -> str:
    if value is None:
        return ""
    return value.isoformat()


def _date_label(value: date | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%d %b %Y")


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


async def _department_options(tenant_id: PydanticObjectId) -> list[InstitutionFieldOption]:
    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    opts = [InstitutionFieldOption(value="", label="Select department")]
    for dept in sorted(departments, key=lambda d: (d.name or "").lower()):
        opts.append(InstitutionFieldOption(value=str(dept.id), label=dept.name or dept.department_code))
    return opts


async def _reporting_options(tenant_id: PydanticObjectId) -> list[InstitutionFieldOption]:
    faculty = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).to_list()
    departments = await InstitutionDepartment.find(Eq(InstitutionDepartment.tenant_id, tenant_id)).to_list()
    dept_by_id = {d.id: d for d in departments}
    opts = [InstitutionFieldOption(value="", label="Select reporting manager")]
    for record in faculty:
        designation = (record.designation or "").lower()
        if "hod" not in designation and "head" not in designation:
            continue
        dept = dept_by_id.get(record.department_id) if record.department_id else None
        dept_code = (dept.department_code if dept else "Unit").upper()
        label = f"HOD, {dept_code}"
        opts.append(InstitutionFieldOption(value=label, label=label))
    return opts


async def _employee_picker(tenant_id: PydanticObjectId) -> list[FacultyAssignmentEmployeeOption]:
    faculty = await FacultyRecord.find(Eq(FacultyRecord.tenant_id, tenant_id)).sort("-updated_at").limit(16).to_list()
    rows: list[FacultyAssignmentEmployeeOption] = []
    for record in faculty:
        user = await User.get(record.user_id)
        if user is None:
            continue
        employee = await EmployeeRecord.find_one(
            Eq(EmployeeRecord.tenant_id, tenant_id),
            Eq(EmployeeRecord.user_id, record.user_id),
        )
        emp_id = (employee.employee_id if employee else None) or record.faculty_code or "—"
        rows.append(
            FacultyAssignmentEmployeeOption(
                record_id=str(record.id),
                label=f"{user.full_name} · {emp_id}",
                employee_id_label=emp_id,
            )
        )
    return rows


async def _employee_options(tenant_id: PydanticObjectId) -> list[InstitutionFieldOption]:
    picker = await _employee_picker(tenant_id)
    opts = [InstitutionFieldOption(value="", label="Select employee")]
    for row in picker:
        opts.append(InstitutionFieldOption(value=row.record_id, label=row.label))
    return opts


async def _resolve_faculty(tenant_id: PydanticObjectId, record_id_raw: str) -> tuple[FacultyRecord, User, EmployeeRecord | None]:
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
    return record, user, employee


def _stored_reporting(employee: EmployeeRecord | None) -> str:
    if employee is None:
        return ""
    hr = employee.confidential_hr or {}
    return str(hr.get("reporting_to") or "")


async def _reporting_label_for_dept(tenant_id: PydanticObjectId, dept_id: PydanticObjectId | None) -> str:
    if dept_id is None:
        return "HOD"
    dept = await InstitutionDepartment.get(dept_id)
    if dept is None or dept.tenant_id != tenant_id:
        return "HOD"
    code = (dept.department_code or dept.name or "Unit")[:12].upper()
    return f"HOD, {code}"


async def _history_items(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    designation: str | None,
    joining_date: date | None,
) -> list[DepartmentDesignationHistoryItem]:
    items: list[DepartmentDesignationHistoryItem] = []
    history = await FacultyEmploymentHistory.find(
        Eq(FacultyEmploymentHistory.tenant_id, tenant_id),
        Eq(FacultyEmploymentHistory.user_id, user_id),
    ).sort("-created_at").limit(6).to_list()
    assignments = await FacultyDepartmentAssignment.find(
        Eq(FacultyDepartmentAssignment.tenant_id, tenant_id),
        Eq(FacultyDepartmentAssignment.user_id, user_id),
    ).sort("-created_at").limit(6).to_list()

    if joining_date and designation:
        items.append(
            DepartmentDesignationHistoryItem(
                key="joined",
                title=f"Joined as {designation}",
                date_label=_date_label(joining_date),
                tone="success",
            )
        )
    for row in assignments[:2]:
        dept = await InstitutionDepartment.get(row.department_id) if row.department_id else None
        dept_name = dept.name if dept else "department"
        items.append(
            DepartmentDesignationHistoryItem(
                key=f"dept-{row.id}",
                title=f"Placed under {dept_name}",
                date_label=_date_label(row.effective_from or (row.created_at.date() if row.created_at else None)),
                tone="info",
            )
        )
    for row in history:
        if row.event_type == "designation_assignment" and row.note:
            items.append(
                DepartmentDesignationHistoryItem(
                    key=f"hist-{row.id}",
                    title=row.note[:120],
                    date_label=_date_label(row.effective_date or (row.created_at.date() if row.created_at else None)),
                    tone="muted",
                )
            )
    return items[:4]


def _approval_steps(
    reporting_label: str,
    *,
    has_unsaved_changes: bool,
) -> list[DepartmentDesignationApprovalStep]:
    if has_unsaved_changes:
        return [
            DepartmentDesignationApprovalStep(
                key="hod",
                label=reporting_label,
                status_label="Approved",
                tone="success",
            ),
            DepartmentDesignationApprovalStep(
                key="college_admin",
                label="College Admin",
                status_label="Pending",
                tone="warning",
            ),
        ]
    return [
        DepartmentDesignationApprovalStep(
            key="hod",
            label=reporting_label,
            status_label="Approved",
            tone="success",
        ),
        DepartmentDesignationApprovalStep(
            key="college_admin",
            label="College Admin",
            status_label="Approved",
            tone="success",
        ),
    ]


async def _form_for_record(
    record: FacultyRecord,
    user: User,
    employee: EmployeeRecord | None,
) -> DepartmentDesignationAssignmentFormValues:
    return DepartmentDesignationAssignmentFormValues(
        record_id=str(record.id),
        department_id=str(record.department_id) if record.department_id else "",
        designation=record.designation or "",
        reporting_to=_stored_reporting(employee),
        effective_from=_format_date(employee.joining_date if employee else None) or utcnow().date().isoformat(),
        reason="",
    )


async def get_department_designation_assignment_page(
    scope: AccessScope,
    record_id_raw: str | None = None,
) -> DepartmentDesignationAssignmentPageRead:
    authorize(scope, Permission.FACULTY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    if not record_id_raw or not record_id_raw.strip():
        picker = await _employee_picker(tenant_id)
        return DepartmentDesignationAssignmentPageRead(
            page_title="Department & Designation Assignment",
            page_subtitle="Assign department, designation and reporting line",
            cancel_label="Cancel",
            cancel_href="/college-admin/faculty/faculty-directory",
            save_label="Save assignment",
            requires_record=True,
            select_employee_title="Select a faculty member",
            select_employee_hint="Choose who you are assigning. You can also open this page from the faculty directory.",
            faculty_directory_href="/college-admin/faculty/faculty-directory",
            faculty_directory_label="Faculty directory",
            picker_rows=picker,
            field_meta=_FIELD_META,
            employee_options=await _employee_options(tenant_id),
            department_options=await _department_options(tenant_id),
            designation_options=await _designation_options(tenant_id),
            reporting_to_options=await _reporting_options(tenant_id),
            footer_disclaimer="Live institutional data · Faculty and employee records · All times IST",
            footer_snapshot_label="Snapshot",
            generated_at=now,
        )

    record, user, employee = await _resolve_faculty(tenant_id, record_id_raw)
    form = await _form_for_record(record, user, employee)
    emp_id = (employee.employee_id if employee else None) or record.faculty_code or "—"
    employee_display = f"{user.full_name} · {emp_id}"
    reporting_default = form.reporting_to or await _reporting_label_for_dept(tenant_id, record.department_id)
    if not form.reporting_to:
        form.reporting_to = reporting_default

    history = await _history_items(
        tenant_id,
        record.user_id,
        designation=record.designation,
        joining_date=employee.joining_date if employee else None,
    )

    return DepartmentDesignationAssignmentPageRead(
        page_title="Department & Designation Assignment",
        page_subtitle="Assign department, designation and reporting line",
        cancel_label="Cancel",
        cancel_href="/college-admin/faculty/faculty-directory",
        save_label="Save assignment",
        employee_display=employee_display,
        assignment_section_title="Assignment",
        field_meta=_FIELD_META,
        form=form,
        employee_options=await _employee_options(tenant_id),
        department_options=await _department_options(tenant_id),
        designation_options=await _designation_options(tenant_id),
        reporting_to_options=await _reporting_options(tenant_id),
        history_section_title="Assignment history",
        history_items=history,
        approval_section_title="Approval",
        approval_steps=_approval_steps(reporting_default, has_unsaved_changes=False),
        footer_disclaimer="Live institutional data · Faculty and employee records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def save_department_designation_assignment(
    scope: AccessScope,
    payload: DepartmentDesignationAssignmentSavePayload,
) -> DepartmentDesignationAssignmentPageRead:
    authorize(scope, Permission.FACULTY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    actor_id = scope.user_id
    assert actor_id is not None

    record, user, employee = await _resolve_faculty(tenant_id, payload.record_id)
    raw = payload.values or {}
    form = DepartmentDesignationAssignmentFormValues(
        record_id=payload.record_id,
        department_id=str(raw.get("department_id") or "").strip(),
        designation=str(raw.get("designation") or "").strip(),
        reporting_to=str(raw.get("reporting_to") or "").strip(),
        effective_from=str(raw.get("effective_from") or "").strip(),
        reason=str(raw.get("reason") or "").strip(),
    )
    if not form.department_id or not form.designation or not form.reporting_to:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Department, designation and reporting line are required",
            status_code=422,
        )
    effective = _parse_date(form.effective_from) or utcnow().date()
    dept_id = to_object_id(form.department_id, "department_id")
    dept = await InstitutionDepartment.get(dept_id)
    if dept is None or dept.tenant_id != tenant_id:
        raise AppError(code="VALIDATION_ERROR", message="Invalid department", status_code=422)

    for prev in await FacultyDepartmentAssignment.find(
        Eq(FacultyDepartmentAssignment.tenant_id, tenant_id),
        Eq(FacultyDepartmentAssignment.user_id, record.user_id),
        Eq(FacultyDepartmentAssignment.is_primary, True),
    ).to_list():
        prev.is_primary = False
        prev.effective_to = effective
        await prev.save()

    record.department_id = dept_id
    record.designation = form.designation
    record.updated_by = actor_id
    record.updated_at = utcnow()
    await record.save()

    if employee is None:
        employee = EmployeeRecord(
            tenant_id=tenant_id,
            user_id=record.user_id,
            is_faculty=True,
            employment_status=record.employment_status,
        )
    employee.department_id = dept_id
    employee.designation = form.designation
    hr = dict(employee.confidential_hr or {})
    hr["reporting_to"] = form.reporting_to
    employee.confidential_hr = hr
    employee.updated_by = actor_id
    employee.updated_at = utcnow()
    if employee.id is None:
        await employee.insert()
    else:
        await employee.save()
    await _sync_employee_snapshot(employee)

    user.department_id = dept_id
    user.updated_at = utcnow()
    await user.save()
    await _sync_faculty_profile(record, user)

    await FacultyDepartmentAssignment(
        tenant_id=tenant_id,
        user_id=record.user_id,
        department_id=dept_id,
        is_primary=True,
        effective_from=effective,
        actor_id=actor_id,
    ).insert()

    note = form.reason or f"Designation updated to {form.designation}"
    await FacultyEmploymentHistory(
        tenant_id=tenant_id,
        user_id=record.user_id,
        event_type="designation_assignment",
        note=note,
        effective_date=effective,
        actor_id=actor_id,
    ).insert()

    page = await get_department_designation_assignment_page(scope, str(record.id))
    page.form.reason = form.reason
    page.approval_steps = _approval_steps(form.reporting_to, has_unsaved_changes=False)
    page.history_items = await _history_items(
        tenant_id,
        record.user_id,
        designation=form.designation,
        joining_date=employee.joining_date,
    )
    return page