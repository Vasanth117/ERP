"""HR organization & employment structure."""

from datetime import date

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.college_admin.identity_models import InstitutionDepartment, InstitutionOrganizationUnit
from app.modules.college_admin.identity_schemas import InstitutionDepartmentCreate, InstitutionDepartmentRead, InstitutionDepartmentUpdate
from app.modules.college_admin.models import InstitutionCampus
from app.modules.college_admin.organization_service import (
    assign_department_head,
    create_institution_department,
    get_department_history,
    get_institution_department,
    list_institution_departments,
    list_organization_units,
    update_institution_department,
)
from app.modules.college_admin.identity_schemas import DepartmentHeadAssign
from app.modules.hr.assignment_sync import ensure_current_assignment, institution_dept_for_central
from app.modules.hr.employee_profile_models import HrEmployeeProfile
from app.modules.hr.employee_sync import log_hr_activity, sync_employee_snapshot
from app.modules.hr.enums import HrEmployeeTransferStatus, HrEmploymentClassificationKind, HrStaffActivityType
from app.modules.hr.organization_schemas import (
    AssignmentHistoryItem,
    DepartmentEmployeeStats,
    DepartmentEmployeesRead,
    EmployeeAssignmentRead,
    EmployeeAssignmentUpdate,
    EmployeeTransferCreate,
    EmployeeTransferRead,
    HrDesignationCreate,
    HrDesignationRead,
    HrDesignationUpdate,
    HrEmploymentClassificationRead,
    HrEmploymentClassificationUpsert,
    HrWorkLocationCreate,
    HrWorkLocationRead,
    OrganizationOverview,
    OrgHierarchyNode,
    ReportingHierarchyRead,
    ReportingManagerUpdate,
    TransferApproval,
)
from app.modules.hr.policy import (
    authorize_hr_assignment_manage,
    authorize_hr_org_manage,
    authorize_hr_org_read,
    authorize_hr_transfer_manage,
    require_hr_tenant_scope,
)
from app.modules.hr.structure_models import (
    HrDesignation,
    HrEmployeeAssignmentHistory,
    HrEmployeeCurrentAssignment,
    HrEmployeeTransferRequest,
    HrEmploymentClassification,
    HrReportingManagerHistory,
    HrWorkLocation,
    HrWorkLocationHistory,
)
from app.repositories.user_repository import UserRepository

_user_repo = UserRepository()

_DEFAULT_CLASSIFICATIONS: list[tuple[str, str, HrEmploymentClassificationKind, dict]] = [
    ("PERM", "Permanent", HrEmploymentClassificationKind.TYPE, {"probation_applicable": True}),
    ("TEMP", "Temporary", HrEmploymentClassificationKind.TYPE, {"max_duration_months": 12}),
    ("CONTRACT", "Contract", HrEmploymentClassificationKind.TYPE, {"renewable": True}),
    ("PART_TIME", "Part-time", HrEmploymentClassificationKind.TYPE, {}),
    ("FULL_TIME", "Full-time", HrEmploymentClassificationKind.TYPE, {}),
    ("VISITING", "Visiting faculty", HrEmploymentClassificationKind.CATEGORY, {}),
    ("GUEST", "Guest faculty", HrEmploymentClassificationKind.CATEGORY, {}),
    ("INTERN", "Intern", HrEmploymentClassificationKind.CATEGORY, {}),
    ("CONSULTANT", "Consultant", HrEmploymentClassificationKind.CATEGORY, {}),
    ("ADMIN", "Administrative staff", HrEmploymentClassificationKind.CATEGORY, {}),
]


async def _seed_classifications(tenant_id: PydanticObjectId, actor_id: PydanticObjectId | None) -> None:
    count = await HrEmploymentClassification.find(Eq(HrEmploymentClassification.tenant_id, tenant_id)).count()
    if count:
        return
    for code, label, kind, rules in _DEFAULT_CLASSIFICATIONS:
        await HrEmploymentClassification(
            tenant_id=tenant_id,
            code=code,
            label=label,
            kind=kind,
            rules=rules,
            updated_by=actor_id,
        ).insert()


async def _assert_designation_parent_valid(tenant_id: PydanticObjectId, designation_id: PydanticObjectId | None, parent_id: PydanticObjectId | None) -> None:
    if parent_id is None:
        return
    if designation_id is not None and parent_id == designation_id:
        raise AppError(code="VALIDATION_ERROR", message="Designation cannot be its own parent", status_code=422)
    visited: set[str] = {str(parent_id)}
    current = parent_id
    while current:
        if designation_id is not None and current == designation_id:
            raise AppError(code="VALIDATION_ERROR", message="Circular designation hierarchy", status_code=422)
        parent = await HrDesignation.get(current)
        if parent is None or parent.tenant_id != tenant_id:
            break
        current = parent.parent_designation_id
        if current and str(current) in visited:
            raise AppError(code="VALIDATION_ERROR", message="Circular designation hierarchy", status_code=422)
        if current:
            visited.add(str(current))


async def _assert_no_circular_reporting(tenant_id: PydanticObjectId, employee_user_id: PydanticObjectId, manager_user_id: PydanticObjectId) -> None:
    if employee_user_id == manager_user_id:
        raise AppError(code="VALIDATION_ERROR", message="Employee cannot report to themselves", status_code=422)
    seen = {employee_user_id}
    current = manager_user_id
    for _ in range(25):
        if current in seen:
            raise AppError(code="VALIDATION_ERROR", message="Circular reporting relationship", status_code=422)
        seen.add(current)
        row = await HrEmployeeCurrentAssignment.find_one(
            Eq(HrEmployeeCurrentAssignment.tenant_id, tenant_id),
            Eq(HrEmployeeCurrentAssignment.employee_user_id, current),
        )
        if row is None or row.reporting_manager_user_id is None:
            break
        current = row.reporting_manager_user_id


async def _record_assignment_history(
    tenant_id: PydanticObjectId,
    employee_user_id: PydanticObjectId,
    change_type: str,
    snapshot: dict,
    *,
    reason: str | None,
    effective_from: date | None,
    effective_to: date | None = None,
    approval: dict | None = None,
    transfer_request_id: PydanticObjectId | None = None,
    actor_id: PydanticObjectId | None = None,
) -> None:
    await HrEmployeeAssignmentHistory(
        tenant_id=tenant_id,
        employee_user_id=employee_user_id,
        change_type=change_type,
        assignment_snapshot=snapshot,
        effective_from=effective_from,
        effective_to=effective_to,
        reason=reason,
        approval=approval or {},
        transfer_request_id=transfer_request_id,
        actor_id=actor_id,
    ).insert()


def _build_dept_tree(rows: list[InstitutionDepartment], parent_id: str | None = None) -> list[OrgHierarchyNode]:
    nodes: list[OrgHierarchyNode] = []
    for row in rows:
        pid = str(row.parent_department_id) if row.parent_department_id else None
        if pid != parent_id:
            continue
        node = OrgHierarchyNode(
            node_id=str(row.id),
            node_type="department",
            code=row.department_code,
            name=row.name,
            parent_id=pid,
            status=row.status.value,
            head_user_id=str(row.head_user_id) if row.head_user_id else None,
            children=_build_dept_tree(rows, str(row.id)),
        )
        nodes.append(node)
    return nodes


async def get_organization_overview(scope: AccessScope) -> OrganizationOverview:
    authorize_hr_org_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    departments = await InstitutionDepartment.find(Eq(InstitutionDepartment.tenant_id, tenant_id)).to_list()
    units = await InstitutionOrganizationUnit.find(Eq(InstitutionOrganizationUnit.tenant_id, tenant_id)).count()
    campuses = await InstitutionCampus.find(Eq(InstitutionCampus.tenant_id, tenant_id)).count()
    designations = await HrDesignation.find(Eq(HrDesignation.tenant_id, tenant_id), Eq(HrDesignation.is_active, True)).count()
    locations = await HrWorkLocation.find(Eq(HrWorkLocation.tenant_id, tenant_id)).count()
    tree = _build_dept_tree(departments, None)
    org_units = await list_organization_units(scope)
    unit_nodes = [
        OrgHierarchyNode(
            node_id=u.unit_id,
            node_type="organization_unit",
            code=u.unit_code,
            name=u.name,
            parent_id=u.parent_unit_id,
            status=u.status.value,
            head_user_id=u.head_user_id,
            children=[],
        )
        for u in org_units
    ]
    return OrganizationOverview(
        department_count=len(departments),
        organization_unit_count=units,
        campus_count=campuses,
        active_designations=designations,
        work_locations=locations,
        hierarchy=[*unit_nodes, *tree],
    )


async def hr_create_department(scope: AccessScope, payload: InstitutionDepartmentCreate) -> InstitutionDepartmentRead:
    authorize_hr_org_manage(scope)
    return await create_institution_department(scope, payload)


async def hr_list_departments(scope: AccessScope, pagination: Pagination) -> Page[InstitutionDepartmentRead]:
    authorize_hr_org_read(scope)
    return await list_institution_departments(scope, pagination)


async def hr_get_department(scope: AccessScope, department_id: str) -> InstitutionDepartmentRead:
    authorize_hr_org_read(scope)
    return await get_institution_department(scope, to_object_id(department_id, "department_id"))


async def hr_update_department(scope: AccessScope, department_id: str, payload: InstitutionDepartmentUpdate) -> InstitutionDepartmentRead:
    authorize_hr_org_manage(scope)
    return await update_institution_department(scope, to_object_id(department_id, "department_id"), payload)


async def hr_assign_department_head(scope: AccessScope, department_id: str, payload: DepartmentHeadAssign) -> InstitutionDepartmentRead:
    authorize_hr_org_manage(scope)
    return await assign_department_head(scope, to_object_id(department_id, "department_id"), payload)


async def hr_department_history(scope: AccessScope, department_id: str):
    authorize_hr_org_read(scope)
    return await get_department_history(scope, to_object_id(department_id, "department_id"))


async def department_employees(scope: AccessScope, department_id: str, pagination: Pagination) -> DepartmentEmployeesRead:
    authorize_hr_org_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    dept_oid = to_object_id(department_id, "department_id")
    dept = await get_institution_department(scope, dept_oid)
    if dept.central_department_id is None:
        raise AppError(code="VALIDATION_ERROR", message="Department has no central mapping", status_code=422)
    central = to_object_id(dept.central_department_id, "central_department_id")
    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.department_id, central)).to_list()
    stats = DepartmentEmployeeStats(department_id=department_id, total_employees=len(employees))
    for emp in employees:
        if emp.employment_status == FacultyEmploymentStatus.ACTIVE:
            stats.active_employees += 1
        if emp.employment_status == FacultyEmploymentStatus.PROBATION:
            stats.probation_employees += 1
    ids = [str(e.user_id) for e in employees]
    start = pagination.offset
    end = start + pagination.limit
    return DepartmentEmployeesRead(department=dept, stats=stats, employee_user_ids=ids[start:end])


async def upsert_designation(scope: AccessScope, payload: HrDesignationCreate) -> HrDesignationRead:
    authorize_hr_org_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    code = payload.designation_code.strip().upper()
    parent_id = to_object_id(payload.parent_designation_id, "parent_designation_id") if payload.parent_designation_id else None
    dept_ids = [to_object_id(x, "applicable_department_id") for x in payload.applicable_department_ids]
    existing = await HrDesignation.find_one(Eq(HrDesignation.tenant_id, tenant_id), Eq(HrDesignation.designation_code, code))
    if existing:
        await _assert_designation_parent_valid(tenant_id, existing.id, parent_id)
        existing.name = payload.name
        existing.description = payload.description
        existing.category = payload.category
        existing.hierarchy_level = payload.hierarchy_level
        existing.parent_designation_id = parent_id
        existing.applicable_department_ids = dept_ids
        existing.applicable_employment_categories = payload.applicable_employment_categories
        existing.updated_by = scope.user_id
        existing.updated_at = utcnow()
        await existing.save()
        doc = existing
    else:
        await _assert_designation_parent_valid(tenant_id, None, parent_id)
        doc = HrDesignation(
            tenant_id=tenant_id,
            designation_code=code,
            name=payload.name,
            description=payload.description,
            category=payload.category,
            hierarchy_level=payload.hierarchy_level,
            parent_designation_id=parent_id,
            applicable_department_ids=dept_ids,
            applicable_employment_categories=payload.applicable_employment_categories,
            updated_by=scope.user_id,
        )
        await doc.insert()
    count = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.designation, doc.name)).count()
    return HrDesignationRead.from_doc(doc, employee_count=count)


async def list_designations(scope: AccessScope, pagination: Pagination) -> Page[HrDesignationRead]:
    authorize_hr_org_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    query = HrDesignation.find(Eq(HrDesignation.tenant_id, tenant_id))
    total = await query.count()
    rows = await query.sort("+designation_code").skip(pagination.offset).limit(pagination.limit).to_list()
    items = []
    for row in rows:
        count = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.designation, row.name)).count()
        items.append(HrDesignationRead.from_doc(row, employee_count=count))
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def update_designation(scope: AccessScope, designation_id: str, payload: HrDesignationUpdate) -> HrDesignationRead:
    authorize_hr_org_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc = await HrDesignation.get(to_object_id(designation_id, "designation_id"))
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Designation not found", status_code=404)
    data = payload.model_dump(exclude_none=True)
    if "parent_designation_id" in data:
        parent = to_object_id(data["parent_designation_id"], "parent_designation_id") if data["parent_designation_id"] else None
        await _assert_designation_parent_valid(tenant_id, doc.id, parent)
        doc.parent_designation_id = parent
        data.pop("parent_designation_id", None)
    if "applicable_department_ids" in data:
        doc.applicable_department_ids = [to_object_id(x, "applicable_department_id") for x in data.pop("applicable_department_ids")]
    for key, value in data.items():
        setattr(doc, key, value)
    doc.updated_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    count = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.designation, doc.name)).count()
    return HrDesignationRead.from_doc(doc, employee_count=count)


async def list_employment_classifications(scope: AccessScope) -> list[HrEmploymentClassificationRead]:
    authorize_hr_org_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    await _seed_classifications(tenant_id, scope.user_id)
    rows = await HrEmploymentClassification.find(Eq(HrEmploymentClassification.tenant_id, tenant_id)).sort("+kind", "+code").to_list()
    return [HrEmploymentClassificationRead.from_doc(row) for row in rows]


async def upsert_employment_classification(scope: AccessScope, payload: HrEmploymentClassificationUpsert) -> HrEmploymentClassificationRead:
    authorize_hr_org_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    code = payload.code.strip().upper()
    doc = await HrEmploymentClassification.find_one(
        Eq(HrEmploymentClassification.tenant_id, tenant_id),
        Eq(HrEmploymentClassification.kind, payload.kind),
        Eq(HrEmploymentClassification.code, code),
    )
    if doc:
        doc.label = payload.label
        doc.description = payload.description
        doc.rules = payload.rules
        doc.is_active = payload.is_active
        doc.updated_by = scope.user_id
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = HrEmploymentClassification(
            tenant_id=tenant_id,
            code=code,
            label=payload.label,
            kind=payload.kind,
            description=payload.description,
            rules=payload.rules,
            is_active=payload.is_active,
            updated_by=scope.user_id,
        )
        await doc.insert()
    return HrEmploymentClassificationRead.from_doc(doc)


async def create_work_location(scope: AccessScope, payload: HrWorkLocationCreate) -> HrWorkLocationRead:
    authorize_hr_org_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    code = payload.location_code.strip().upper()
    campus_id = to_object_id(payload.campus_id, "campus_id")
    campus = await InstitutionCampus.get(campus_id)
    if campus is None or campus.tenant_id != tenant_id:
        raise AppError(code="VALIDATION_ERROR", message="Invalid campus", status_code=422)
    if await HrWorkLocation.find_one(Eq(HrWorkLocation.tenant_id, tenant_id), Eq(HrWorkLocation.location_code, code)):
        raise AppError(code="CONFLICT", message="Work location code already exists", status_code=409)
    dept_id = to_object_id(payload.institution_department_id, "institution_department_id") if payload.institution_department_id else None
    row = HrWorkLocation(
        tenant_id=tenant_id,
        campus_id=campus_id,
        location_code=code,
        name=payload.name,
        office_label=payload.office_label,
        institution_department_id=dept_id,
        updated_by=scope.user_id,
    )
    await row.insert()
    return HrWorkLocationRead.from_doc(row)


async def list_work_locations(scope: AccessScope, pagination: Pagination) -> Page[HrWorkLocationRead]:
    authorize_hr_org_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    query = HrWorkLocation.find(Eq(HrWorkLocation.tenant_id, tenant_id))
    total = await query.count()
    rows = await query.sort("+location_code").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[HrWorkLocationRead.from_doc(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def get_employee_assignment(scope: AccessScope, employee_user_id: str) -> EmployeeAssignmentRead:
    authorize_hr_org_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(employee_user_id, "employee_user_id")
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, uid))
    if employee is None:
        raise AppError(code="NOT_FOUND", message="Employee not found", status_code=404)
    profile = await HrEmployeeProfile.find_one(Eq(HrEmployeeProfile.tenant_id, tenant_id), Eq(HrEmployeeProfile.user_id, uid))
    row = await ensure_current_assignment(tenant_id, employee, profile, actor_id=scope.user_id)
    return EmployeeAssignmentRead.from_doc(row)


async def update_employee_assignment(scope: AccessScope, employee_user_id: str, payload: EmployeeAssignmentUpdate) -> EmployeeAssignmentRead:
    authorize_hr_assignment_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(employee_user_id, "employee_user_id")
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, uid))
    if employee is None:
        raise AppError(code="NOT_FOUND", message="Employee not found", status_code=404)
    profile = await HrEmployeeProfile.find_one(Eq(HrEmployeeProfile.tenant_id, tenant_id), Eq(HrEmployeeProfile.user_id, uid))
    row = await ensure_current_assignment(tenant_id, employee, profile, actor_id=scope.user_id)
    before = row.model_dump(mode="json")

    if payload.institution_department_id:
        inst = await InstitutionDepartment.get(to_object_id(payload.institution_department_id, "institution_department_id"))
        if inst is None or inst.tenant_id != tenant_id:
            raise AppError(code="VALIDATION_ERROR", message="Invalid department", status_code=422)
        row.institution_department_id = inst.id
        row.central_department_id = inst.central_department_id
        employee.department_id = inst.central_department_id
    if payload.designation_id:
        des = await HrDesignation.get(to_object_id(payload.designation_id, "designation_id"))
        if des is None or des.tenant_id != tenant_id or not des.is_active:
            raise AppError(code="VALIDATION_ERROR", message="Invalid designation", status_code=422)
        row.designation_id = des.id
        row.designation_code = des.designation_code
        employee.designation = des.name
    if payload.employment_type_code:
        row.employment_type_code = payload.employment_type_code
        employee.employment_type = payload.employment_type_code
    if payload.employment_category_code and profile:
        row.employment_category_code = payload.employment_category_code
        profile.employee_category = payload.employment_category_code
        profile.updated_at = utcnow()
        await profile.save()
    if payload.campus_id:
        campus_id = to_object_id(payload.campus_id, "campus_id")
        row.campus_id = campus_id
        employee.campus_id = campus_id
    if payload.work_location_id:
        loc = await HrWorkLocation.get(to_object_id(payload.work_location_id, "work_location_id"))
        if loc is None or loc.tenant_id != tenant_id:
            raise AppError(code="VALIDATION_ERROR", message="Invalid work location", status_code=422)
        row.work_location_id = loc.id
    if payload.reporting_manager_user_id:
        manager_id = to_object_id(payload.reporting_manager_user_id, "reporting_manager_user_id")
        await _assert_no_circular_reporting(tenant_id, uid, manager_id)
        row.reporting_manager_user_id = manager_id
        if profile:
            profile.reporting_manager_user_id = manager_id
            profile.updated_at = utcnow()
            await profile.save()
        await HrReportingManagerHistory(
            tenant_id=tenant_id,
            employee_user_id=uid,
            manager_user_id=manager_id,
            effective_from=payload.effective_from or date.today(),
            actor_id=scope.user_id,
            reason=payload.reason,
        ).insert()
    if payload.effective_from:
        row.effective_from = payload.effective_from
    row.updated_by = scope.user_id
    row.updated_at = utcnow()
    employee.updated_at = utcnow()
    employee.updated_by = scope.user_id
    await employee.save()
    await row.save()
    await sync_employee_snapshot(employee)
    await _record_assignment_history(
        tenant_id,
        uid,
        "assignment_update",
        {"before": before, "after": row.model_dump(mode="json")},
        reason=payload.reason,
        effective_from=payload.effective_from or date.today(),
        actor_id=scope.user_id,
    )
    await log_hr_activity(
        tenant_id,
        HrStaffActivityType.DEPARTMENT_CHANGED,
        "Employee assignment updated",
        actor_id=scope.user_id,
        employee_user_id=uid,
        department_id=row.institution_department_id,
        campus_id=row.campus_id,
    )
    return EmployeeAssignmentRead.from_doc(row)


async def update_reporting_manager(scope: AccessScope, employee_user_id: str, payload: ReportingManagerUpdate) -> EmployeeAssignmentRead:
    assign = EmployeeAssignmentUpdate(
        reporting_manager_user_id=payload.manager_user_id,
        effective_from=payload.effective_from,
        reason=payload.reason,
    )
    return await update_employee_assignment(scope, employee_user_id, assign)


async def get_reporting_hierarchy(scope: AccessScope, employee_user_id: str) -> ReportingHierarchyRead:
    authorize_hr_org_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(employee_user_id, "employee_user_id")
    chain: list[str] = []
    current = uid
    for _ in range(25):
        row = await HrEmployeeCurrentAssignment.find_one(
            Eq(HrEmployeeCurrentAssignment.tenant_id, tenant_id),
            Eq(HrEmployeeCurrentAssignment.employee_user_id, current),
        )
        if row is None or row.reporting_manager_user_id is None:
            break
        manager = row.reporting_manager_user_id
        chain.append(str(manager))
        current = manager
    directs = await HrEmployeeCurrentAssignment.find(
        Eq(HrEmployeeCurrentAssignment.tenant_id, tenant_id),
        Eq(HrEmployeeCurrentAssignment.reporting_manager_user_id, uid),
    ).to_list()
    return ReportingHierarchyRead(
        employee_user_id=employee_user_id,
        chain=chain,
        direct_reports=[str(d.employee_user_id) for d in directs],
    )


async def create_transfer_request(scope: AccessScope, employee_user_id: str, payload: EmployeeTransferCreate) -> EmployeeTransferRead:
    authorize_hr_transfer_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(employee_user_id, "employee_user_id")
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, uid))
    if employee is None:
        raise AppError(code="NOT_FOUND", message="Employee not found", status_code=404)
    profile = await HrEmployeeProfile.find_one(Eq(HrEmployeeProfile.tenant_id, tenant_id), Eq(HrEmployeeProfile.user_id, uid))
    current = await ensure_current_assignment(tenant_id, employee, profile, actor_id=scope.user_id)
    active = await HrEmployeeTransferRequest.find_one(
        Eq(HrEmployeeTransferRequest.tenant_id, tenant_id),
        Eq(HrEmployeeTransferRequest.employee_user_id, uid),
        In(
            HrEmployeeTransferRequest.status,
            [HrEmployeeTransferStatus.DRAFT, HrEmployeeTransferStatus.PENDING_APPROVAL, HrEmployeeTransferStatus.APPROVED, HrEmployeeTransferStatus.SCHEDULED],
        ),
    )
    if active:
        raise AppError(code="CONFLICT", message="An active transfer request already exists", status_code=409)
    to_central = None
    if payload.to_institution_department_id:
        inst = await InstitutionDepartment.get(to_object_id(payload.to_institution_department_id, "to_institution_department_id"))
        if inst is None or inst.tenant_id != tenant_id:
            raise AppError(code="VALIDATION_ERROR", message="Invalid target department", status_code=422)
        to_central = inst.central_department_id
    elif payload.to_central_department_id:
        to_central = to_object_id(payload.to_central_department_id, "to_central_department_id")
    status = HrEmployeeTransferStatus.PENDING_APPROVAL if payload.requires_approval else HrEmployeeTransferStatus.APPROVED
    row = HrEmployeeTransferRequest(
        tenant_id=tenant_id,
        employee_user_id=uid,
        status=status,
        from_assignment=current.model_dump(mode="json"),
        to_institution_department_id=to_object_id(payload.to_institution_department_id, "to_institution_department_id") if payload.to_institution_department_id else None,
        to_central_department_id=to_central,
        to_designation_id=to_object_id(payload.to_designation_id, "to_designation_id") if payload.to_designation_id else None,
        to_employment_type_code=payload.to_employment_type_code,
        to_employment_category_code=payload.to_employment_category_code,
        to_campus_id=to_object_id(payload.to_campus_id, "to_campus_id") if payload.to_campus_id else None,
        to_work_location_id=to_object_id(payload.to_work_location_id, "to_work_location_id") if payload.to_work_location_id else None,
        to_reporting_manager_user_id=to_object_id(payload.to_reporting_manager_user_id, "to_reporting_manager_user_id")
        if payload.to_reporting_manager_user_id
        else None,
        effective_date=payload.effective_date,
        reason=payload.reason,
        requires_approval=payload.requires_approval,
        requested_by=scope.user_id,
        approved_by=None if payload.requires_approval else scope.user_id,
        approved_at=None if payload.requires_approval else utcnow(),
    )
    await row.insert()
    if not payload.requires_approval:
        await _apply_transfer_if_due(tenant_id, row)
    return EmployeeTransferRead.from_doc(row)


async def review_transfer(scope: AccessScope, transfer_id: str, payload: TransferApproval) -> EmployeeTransferRead:
    authorize_hr_transfer_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    row = await HrEmployeeTransferRequest.get(to_object_id(transfer_id, "transfer_id"))
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Transfer request not found", status_code=404)
    if row.status != HrEmployeeTransferStatus.PENDING_APPROVAL:
        raise AppError(code="CONFLICT", message="Transfer is not awaiting approval", status_code=409)
    if payload.decision == "approved":
        row.status = HrEmployeeTransferStatus.APPROVED
        row.approved_by = scope.user_id
        row.approved_at = utcnow()
        row.approval_note = payload.note
        await row.save()
        await _apply_transfer_if_due(tenant_id, row)
    else:
        row.status = HrEmployeeTransferStatus.REJECTED
        row.rejection_note = payload.note
        await row.save()
    return EmployeeTransferRead.from_doc(row)


async def _apply_transfer_if_due(tenant_id: PydanticObjectId, row: HrEmployeeTransferRequest) -> None:
    if row.status not in {HrEmployeeTransferStatus.APPROVED, HrEmployeeTransferStatus.SCHEDULED}:
        return
    if row.effective_date > date.today():
        row.status = HrEmployeeTransferStatus.SCHEDULED
        await row.save()
        return
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, row.employee_user_id))
    if employee is None:
        return
    profile = await HrEmployeeProfile.find_one(Eq(HrEmployeeProfile.tenant_id, tenant_id), Eq(HrEmployeeProfile.user_id, row.employee_user_id))
    current = await ensure_current_assignment(tenant_id, employee, profile, actor_id=row.approved_by)
    before = current.model_dump(mode="json")
    if row.to_central_department_id:
        employee.department_id = row.to_central_department_id
        current.central_department_id = row.to_central_department_id
        current.institution_department_id = row.to_institution_department_id
        inst = await institution_dept_for_central(tenant_id, row.to_central_department_id)
        if inst:
            current.institution_department_id = inst.id
            current.organization_unit_id = inst.organization_unit_id
    if row.to_designation_id:
        des = await HrDesignation.get(row.to_designation_id)
        if des:
            employee.designation = des.name
            current.designation_id = des.id
            current.designation_code = des.designation_code
    if row.to_employment_type_code:
        employee.employment_type = row.to_employment_type_code
        current.employment_type_code = row.to_employment_type_code
    if row.to_employment_category_code and profile:
        profile.employee_category = row.to_employment_category_code
        current.employment_category_code = row.to_employment_category_code
        profile.updated_at = utcnow()
        await profile.save()
    if row.to_campus_id:
        prev_campus = employee.campus_id
        employee.campus_id = row.to_campus_id
        current.campus_id = row.to_campus_id
        await HrWorkLocationHistory(
            tenant_id=tenant_id,
            employee_user_id=row.employee_user_id,
            from_campus_id=prev_campus,
            to_campus_id=row.to_campus_id,
            from_work_location_id=current.work_location_id,
            to_work_location_id=row.to_work_location_id,
            effective_from=row.effective_date,
            reason=row.reason,
            actor_id=row.approved_by,
        ).insert()
    if row.to_work_location_id:
        current.work_location_id = row.to_work_location_id
    if row.to_reporting_manager_user_id:
        await _assert_no_circular_reporting(tenant_id, row.employee_user_id, row.to_reporting_manager_user_id)
        current.reporting_manager_user_id = row.to_reporting_manager_user_id
        if profile:
            profile.reporting_manager_user_id = row.to_reporting_manager_user_id
            profile.updated_at = utcnow()
            await profile.save()
    employee.employment_status = FacultyEmploymentStatus.ACTIVE
    employee.updated_at = utcnow()
    await employee.save()
    current.effective_from = row.effective_date
    current.updated_at = utcnow()
    await current.save()
    await sync_employee_snapshot(employee)
    row.status = HrEmployeeTransferStatus.APPLIED
    row.applied_at = utcnow()
    await row.save()
    await _record_assignment_history(
        tenant_id,
        row.employee_user_id,
        "transfer",
        {"before": before, "after": current.model_dump(mode="json")},
        reason=row.reason,
        effective_from=row.effective_date,
        approval={"approved_by": str(row.approved_by) if row.approved_by else None, "note": row.approval_note},
        transfer_request_id=row.id,
        actor_id=row.approved_by,
    )
    await log_hr_activity(
        tenant_id,
        HrStaffActivityType.DEPARTMENT_CHANGED,
        "Employee transfer applied",
        actor_id=row.approved_by,
        employee_user_id=row.employee_user_id,
        department_id=current.institution_department_id,
        campus_id=current.campus_id,
        resource_type="hr_transfer",
        resource_id=str(row.id),
    )


async def process_due_transfers(scope: AccessScope) -> dict:
    authorize_hr_transfer_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rows = await HrEmployeeTransferRequest.find(
        Eq(HrEmployeeTransferRequest.tenant_id, tenant_id),
        Eq(HrEmployeeTransferRequest.status, HrEmployeeTransferStatus.SCHEDULED),
        Eq(HrEmployeeTransferRequest.effective_date, date.today()),
    ).to_list()
    applied = 0
    for row in rows:
        row.status = HrEmployeeTransferStatus.APPROVED
        await _apply_transfer_if_due(tenant_id, row)
        applied += 1
    return {"processed": applied}


async def assignment_history(scope: AccessScope, employee_user_id: str, pagination: Pagination) -> Page[AssignmentHistoryItem]:
    authorize_hr_org_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(employee_user_id, "employee_user_id")
    query = HrEmployeeAssignmentHistory.find(
        Eq(HrEmployeeAssignmentHistory.tenant_id, tenant_id),
        Eq(HrEmployeeAssignmentHistory.employee_user_id, uid),
    )
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        AssignmentHistoryItem(
            change_type=r.change_type,
            assignment_snapshot=r.assignment_snapshot,
            effective_from=r.effective_from,
            effective_to=r.effective_to,
            reason=r.reason,
            approval=r.approval,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)