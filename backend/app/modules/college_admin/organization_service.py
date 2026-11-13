"""Institution department and organization management."""

from datetime import date

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.core.exceptions import AppError
from app.modules.college_admin.identity_models import (
    DepartmentHeadAssignment,
    DepartmentHistory,
    DepartmentHierarchy,
    DepartmentStaffAssociation,
    DepartmentStatus,
    InstitutionDepartment,
    InstitutionOrganizationUnit,
)
from app.modules.college_admin.identity_schemas import (
    DepartmentHeadAssign,
    DepartmentHistoryRead,
    DepartmentTransfer,
    InstitutionDepartmentCreate,
    InstitutionDepartmentRead,
    InstitutionDepartmentUpdate,
    OrganizationUnitCreate,
    OrganizationUnitRead,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.tenants.models import Department


async def _record_department_history(
    *,
    tenant_id: PydanticObjectId,
    department_id: PydanticObjectId,
    change_type: str,
    snapshot: dict,
    actor_id: PydanticObjectId | None,
) -> None:
    await DepartmentHistory(
        tenant_id=tenant_id,
        department_id=department_id,
        change_type=change_type,
        snapshot=snapshot,
        actor_id=actor_id,
    ).insert()


async def _rebuild_hierarchy_for_department(tenant_id: PydanticObjectId, department_id: PydanticObjectId) -> None:
    await DepartmentHierarchy.find(
        Eq(DepartmentHierarchy.tenant_id, tenant_id),
        Eq(DepartmentHierarchy.descendant_id, department_id),
    ).delete()
    dept = await InstitutionDepartment.get(department_id)
    if dept is None:
        return
    await DepartmentHierarchy(
        tenant_id=tenant_id,
        ancestor_id=department_id,
        descendant_id=department_id,
        depth=0,
    ).insert()
    parent_id = dept.parent_department_id
    depth = 1
    visited: set[str] = {str(department_id)}
    while parent_id is not None:
        if str(parent_id) in visited:
            raise AppError(code="VALIDATION_ERROR", message="Circular hierarchy detected", status_code=422)
        visited.add(str(parent_id))
        await DepartmentHierarchy(
            tenant_id=tenant_id,
            ancestor_id=parent_id,
            descendant_id=department_id,
            depth=depth,
        ).insert()
        parent = await InstitutionDepartment.get(parent_id)
        if parent is None:
            break
        parent_id = parent.parent_department_id
        depth += 1


async def _assert_department_parent_valid(
    tenant_id: PydanticObjectId,
    department_id: PydanticObjectId | None,
    parent_id: PydanticObjectId | None,
) -> None:
    if parent_id is None:
        return
    if department_id is not None and parent_id == department_id:
        raise AppError(code="VALIDATION_ERROR", message="Department cannot be its own parent", status_code=422)
    parent = await InstitutionDepartment.get(parent_id)
    if parent is None or parent.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Parent department not found", status_code=404)
    if department_id is not None:
        cycle = await DepartmentHierarchy.find_one(
            Eq(DepartmentHierarchy.tenant_id, tenant_id),
            Eq(DepartmentHierarchy.ancestor_id, department_id),
            Eq(DepartmentHierarchy.descendant_id, parent_id),
        )
        if cycle is not None:
            raise AppError(code="VALIDATION_ERROR", message="Circular hierarchy is not allowed", status_code=422)


def _parse_campus_ids(raw: list[str] | None) -> list[PydanticObjectId]:
    if not raw:
        return []
    return [to_object_id(item, "campus_id") for item in raw]


async def create_organization_unit(scope: AccessScope, payload: OrganizationUnitCreate) -> OrganizationUnitRead:
    authorize(scope, Permission.INSTITUTION_ORG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    code = payload.unit_code.upper()
    if await InstitutionOrganizationUnit.find_one(Eq(InstitutionOrganizationUnit.tenant_id, tenant_id), Eq(InstitutionOrganizationUnit.unit_code, code)):
        raise AppError(code="CONFLICT", message="Organization unit code already exists", status_code=409)
    parent_id = to_object_id(payload.parent_unit_id, "parent_unit_id") if payload.parent_unit_id else None
    doc = InstitutionOrganizationUnit(
        tenant_id=tenant_id,
        unit_code=code,
        name=payload.name,
        unit_type=payload.unit_type,
        parent_unit_id=parent_id,
        campus_ids=_parse_campus_ids(payload.campus_ids),
        head_user_id=to_object_id(payload.head_user_id, "head_user_id") if payload.head_user_id else None,
    )
    await doc.insert()
    return OrganizationUnitRead.from_document(doc)


async def list_organization_units(scope: AccessScope) -> list[OrganizationUnitRead]:
    authorize(scope, Permission.INSTITUTION_ORG_READ)
    tenant_id = require_college_tenant_scope(scope)
    rows = await InstitutionOrganizationUnit.find(Eq(InstitutionOrganizationUnit.tenant_id, tenant_id)).sort("+unit_code").to_list()
    return [OrganizationUnitRead.from_document(row) for row in rows]


async def create_institution_department(scope: AccessScope, payload: InstitutionDepartmentCreate) -> InstitutionDepartmentRead:
    authorize(scope, Permission.INSTITUTION_ORG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    code = payload.department_code.upper()
    if await InstitutionDepartment.find_one(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.department_code, code),
    ):
        raise AppError(code="CONFLICT", message="Department code already exists", status_code=409)

    parent_id = to_object_id(payload.parent_department_id, "parent_department_id") if payload.parent_department_id else None
    await _assert_department_parent_valid(tenant_id, None, parent_id)

    central = await Department.find_one(Eq(Department.tenant_id, tenant_id), Eq(Department.code, code))
    if central is None:
        central = Department(tenant_id=tenant_id, name=payload.name, code=code)
        await central.insert()

    org_unit_id = to_object_id(payload.organization_unit_id, "organization_unit_id") if payload.organization_unit_id else None
    reporting_id = (
        to_object_id(payload.reporting_to_department_id, "reporting_to_department_id")
        if payload.reporting_to_department_id
        else None
    )

    doc = InstitutionDepartment(
        tenant_id=tenant_id,
        department_code=code,
        name=payload.name,
        central_department_id=central.id,
        organization_unit_id=org_unit_id,
        parent_department_id=parent_id,
        campus_ids=_parse_campus_ids(payload.campus_ids),
        reporting_to_department_id=reporting_id,
        programme_codes=[c.upper() for c in payload.programme_codes],
        updated_by=scope.user_id,
    )
    await doc.insert()
    await _rebuild_hierarchy_for_department(tenant_id, doc.id)
    await _record_department_history(
        tenant_id=tenant_id,
        department_id=doc.id,
        change_type="created",
        snapshot=doc.model_dump(mode="json"),
        actor_id=scope.user_id,
    )
    from app.modules.audit.service import record_audit

    await record_audit(
        actor_id=scope.user_id,
        action="institution.department.created",
        resource_type="institution_department",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        metadata={"code": code},
    )
    return InstitutionDepartmentRead.from_document(doc)


async def list_institution_departments(scope: AccessScope, pagination: Pagination) -> Page[InstitutionDepartmentRead]:
    authorize(scope, Permission.INSTITUTION_ORG_READ)
    tenant_id = require_college_tenant_scope(scope)
    query = InstitutionDepartment.find(Eq(InstitutionDepartment.tenant_id, tenant_id))
    total = await query.count()
    rows = await query.sort("+department_code").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[InstitutionDepartmentRead.from_document(row) for row in rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_institution_department(scope: AccessScope, department_id: PydanticObjectId) -> InstitutionDepartmentRead:
    authorize(scope, Permission.INSTITUTION_ORG_READ)
    tenant_id = require_college_tenant_scope(scope)
    doc = await InstitutionDepartment.get(department_id)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Department not found", status_code=404)
    return InstitutionDepartmentRead.from_document(doc)


async def update_institution_department(
    scope: AccessScope,
    department_id: PydanticObjectId,
    payload: InstitutionDepartmentUpdate,
) -> InstitutionDepartmentRead:
    authorize(scope, Permission.INSTITUTION_ORG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await InstitutionDepartment.get(department_id)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Department not found", status_code=404)

    before = doc.model_dump(mode="json")
    if payload.parent_department_id is not None:
        parent_id = to_object_id(payload.parent_department_id, "parent_department_id") if payload.parent_department_id else None
        await _assert_department_parent_valid(tenant_id, doc.id, parent_id)
        doc.parent_department_id = parent_id
    if payload.name is not None:
        doc.name = payload.name
        if doc.central_department_id:
            central = await Department.get(doc.central_department_id)
            if central is not None:
                central.name = payload.name
                central.updated_at = utcnow()
                await central.save()
    if payload.organization_unit_id is not None:
        doc.organization_unit_id = to_object_id(payload.organization_unit_id, "organization_unit_id")
    if payload.campus_ids is not None:
        doc.campus_ids = _parse_campus_ids(payload.campus_ids)
    if payload.status is not None:
        doc.status = payload.status
        if doc.central_department_id:
            central = await Department.get(doc.central_department_id)
            if central is not None:
                central.is_active = payload.status == DepartmentStatus.ACTIVE
                central.updated_at = utcnow()
                await central.save()
    if payload.programme_codes is not None:
        doc.programme_codes = [c.upper() for c in payload.programme_codes]
    if payload.reporting_to_department_id is not None:
        doc.reporting_to_department_id = to_object_id(payload.reporting_to_department_id, "reporting_to_department_id")

    doc.updated_at = utcnow()
    doc.updated_by = scope.user_id
    await doc.save()
    await _rebuild_hierarchy_for_department(tenant_id, doc.id)
    await _record_department_history(
        tenant_id=tenant_id,
        department_id=doc.id,
        change_type="updated",
        snapshot={"before": before, "after": doc.model_dump(mode="json")},
        actor_id=scope.user_id,
    )
    return InstitutionDepartmentRead.from_document(doc)


async def assign_department_head(
    scope: AccessScope,
    department_id: PydanticObjectId,
    payload: DepartmentHeadAssign,
) -> InstitutionDepartmentRead:
    authorize(scope, Permission.INSTITUTION_ORG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await InstitutionDepartment.get(department_id)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Department not found", status_code=404)
    user_id = to_object_id(payload.user_id, "user_id")
    effective_from = payload.effective_from.date() if payload.effective_from else date.today()
    doc.head_user_id = user_id
    doc.updated_at = utcnow()
    await doc.save()
    await DepartmentHeadAssignment(
        tenant_id=tenant_id,
        department_id=department_id,
        user_id=user_id,
        effective_from=effective_from,
        assigned_by=scope.user_id,
    ).insert()
    await _record_department_history(
        tenant_id=tenant_id,
        department_id=department_id,
        change_type="head_assigned",
        snapshot={"head_user_id": str(user_id)},
        actor_id=scope.user_id,
    )
    return InstitutionDepartmentRead.from_document(doc)


async def transfer_department(
    scope: AccessScope,
    department_id: PydanticObjectId,
    payload: DepartmentTransfer,
) -> InstitutionDepartmentRead:
    authorize(scope, Permission.INSTITUTION_ORG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await InstitutionDepartment.get(department_id)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Department not found", status_code=404)

    if payload.target_parent_department_id is not None:
        parent_id = to_object_id(payload.target_parent_department_id, "target_parent_department_id")
        await _assert_department_parent_valid(tenant_id, doc.id, parent_id)
        doc.parent_department_id = parent_id
    if payload.target_organization_unit_id is not None:
        doc.organization_unit_id = to_object_id(payload.target_organization_unit_id, "target_organization_unit_id")

    doc.updated_at = utcnow()
    await doc.save()
    await _rebuild_hierarchy_for_department(tenant_id, doc.id)
    await _record_department_history(
        tenant_id=tenant_id,
        department_id=department_id,
        change_type="transferred",
        snapshot={"reason": payload.reason, "department": doc.model_dump(mode="json")},
        actor_id=scope.user_id,
    )
    return InstitutionDepartmentRead.from_document(doc)


async def get_department_history(
    scope: AccessScope,
    department_id: PydanticObjectId,
) -> list[DepartmentHistoryRead]:
    authorize(scope, Permission.INSTITUTION_ORG_READ)
    tenant_id = require_college_tenant_scope(scope)
    doc = await InstitutionDepartment.get(department_id)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Department not found", status_code=404)
    rows = await (
        DepartmentHistory.find(Eq(DepartmentHistory.tenant_id, tenant_id), Eq(DepartmentHistory.department_id, department_id))
        .sort("-created_at")
        .limit(50)
        .to_list()
    )
    return [
        DepartmentHistoryRead(
            change_type=row.change_type,
            snapshot=row.snapshot,
            created_at=row.created_at,
            actor_id=str(row.actor_id) if row.actor_id else None,
        )
        for row in rows
    ]


async def associate_department_staff(
    scope: AccessScope,
    department_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    association_role: str = "staff",
    is_primary: bool = False,
) -> dict:
    authorize(scope, Permission.INSTITUTION_ORG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await InstitutionDepartment.get(department_id)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Department not found", status_code=404)
    row = DepartmentStaffAssociation(
        tenant_id=tenant_id,
        department_id=department_id,
        user_id=user_id,
        association_role=association_role,
        is_primary=is_primary,
    )
    await row.insert()
    return {"status": "ok"}
