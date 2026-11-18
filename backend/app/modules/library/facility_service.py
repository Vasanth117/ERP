"""Library & branch management services."""

from typing import Any
from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.college_admin.library_admin_models import LibraryBookCopyRecord, LibraryBranch
from app.modules.college_admin.models import InstitutionCampus
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.library.facility_access import (
    authorize_facility_read,
    has_institution_library_manage,
    require_facility_manage,
    require_facility_read,
)
from app.modules.library.facility_enums import LibraryConfigEntityType, LibraryStaffAssignmentStatus, LibraryStaffRole
from app.modules.library.facility_models import (
    InstitutionLibrary,
    LibraryConfigurationHistory,
    LibraryHoliday,
    LibraryOperatingHours,
    LibrarySection,
    LibraryShelfLocation,
    LibraryStaffAssignment,
)
from app.modules.library.facility_schemas import (
    BranchOperationalStats,
    InstitutionLibraryCreate,
    InstitutionLibraryRead,
    InstitutionLibraryUpdate,
    LibraryBranchCreate,
    LibraryBranchRead,
    LibraryBranchUpdate,
    LibraryConfigurationHistoryRead,
    LibraryHolidayCreate,
    LibraryHolidayRead,
    LibraryHolidayUpdate,
    LibrarySectionCreate,
    LibrarySectionRead,
    LibrarySectionUpdate,
    LibraryShelfLocationCreate,
    LibraryShelfLocationRead,
    LibraryShelfLocationUpdate,
    LibraryStaffAssignmentCreate,
    LibraryStaffAssignmentRead,
    LibraryStaffAssignmentUpdate,
    OperatingHoursRead,
    OperatingHoursUpsert,
)
from app.modules.library.facility_validation import (
    validate_holiday_range,
    validate_location_parent,
    validate_operating_days,
)
from app.modules.library.library_enums import LibraryCirculationStatus, LibraryCopyStatus, LibraryFineStatus
from app.modules.library.library_models import LibraryCirculation, LibraryCopy, LibraryFine


def _norm_code(code: str) -> str:
    return code.strip().upper()


async def _assert_campus(tenant_id: PydanticObjectId, campus_id: str | None) -> PydanticObjectId | None:
    if not campus_id:
        return None
    oid = to_object_id(campus_id, "campus_id")
    campus = await InstitutionCampus.find_one(Eq(InstitutionCampus.tenant_id, tenant_id), Eq(InstitutionCampus.id, oid))
    if campus is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown campus", status_code=422)
    return oid


async def _get_library(tenant_id: PydanticObjectId, library_code: str) -> InstitutionLibrary:
    doc = await InstitutionLibrary.find_one(
        Eq(InstitutionLibrary.tenant_id, tenant_id),
        Eq(InstitutionLibrary.library_code, _norm_code(library_code)),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Library not found", status_code=404)
    return doc


async def _get_branch(tenant_id: PydanticObjectId, branch_code: str) -> LibraryBranch:
    doc = await LibraryBranch.find_one(
        Eq(LibraryBranch.tenant_id, tenant_id),
        Eq(LibraryBranch.branch_code, _norm_code(branch_code)),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Branch not found", status_code=404)
    return doc


async def _assert_branch_belongs_to_library(branch: LibraryBranch, library_code: str) -> None:
    if branch.library_code and branch.library_code.upper() != _norm_code(library_code):
        raise AppError(code="VALIDATION_ERROR", message="Branch does not belong to library", status_code=422)


async def _record_history(
    tenant_id: PydanticObjectId,
    *,
    actor_id: PydanticObjectId | None,
    entity_type: LibraryConfigEntityType,
    entity_key: str,
    action: str,
    changes: dict[str, Any],
) -> None:
    await LibraryConfigurationHistory(
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_key=entity_key,
        action=action,
        actor_id=actor_id,
        changes=changes,
    ).insert()
    await append_institution_audit(
        tenant_id,
        actor_id=actor_id,
        action=f"library_facility.{action}",
        module="library_facility",
        resource_type=entity_type.value,
        resource_id=entity_key,
        metadata=changes,
    )


def _library_read(doc: InstitutionLibrary) -> InstitutionLibraryRead:
    return InstitutionLibraryRead(
        library_code=doc.library_code,
        name=doc.name,
        description=doc.description,
        campus_id=str(doc.campus_id) if doc.campus_id else None,
        address=doc.address,
        contact_email=doc.contact_email,
        contact_phone=doc.contact_phone,
        operating_status=doc.operating_status,
        is_active=doc.is_active,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


def _branch_read(doc: LibraryBranch) -> LibraryBranchRead:
    return LibraryBranchRead(
        library_code=doc.library_code,
        branch_code=doc.branch_code,
        name=doc.name,
        description=doc.description,
        campus_id=str(doc.campus_id) if doc.campus_id else None,
        address=doc.address,
        contact_email=doc.contact_email,
        contact_phone=doc.contact_phone,
        operating_status=doc.operating_status,
        is_active=doc.is_active,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


async def _assigned_library_codes(scope: AccessScope, tenant_id: PydanticObjectId) -> set[str] | None:
    if has_institution_library_manage(scope):
        return None
    rows = await LibraryStaffAssignment.find(
        Eq(LibraryStaffAssignment.tenant_id, tenant_id),
        Eq(LibraryStaffAssignment.employee_user_id, scope.user_id),
        Eq(LibraryStaffAssignment.status, LibraryStaffAssignmentStatus.ACTIVE),
    ).to_list()
    return {_norm_code(r.library_code) for r in rows}


async def require_staff_assignment_admin(scope: AccessScope, tenant_id: PydanticObjectId, library_code: str) -> None:
    if has_institution_library_manage(scope):
        return
    rows = await LibraryStaffAssignment.find(
        Eq(LibraryStaffAssignment.tenant_id, tenant_id),
        Eq(LibraryStaffAssignment.employee_user_id, scope.user_id),
        Eq(LibraryStaffAssignment.status, LibraryStaffAssignmentStatus.ACTIVE),
    ).to_list()
    for row in rows:
        if row.library_code.upper() == _norm_code(library_code) and row.branch_code is None and row.staff_role == LibraryStaffRole.HEAD_LIBRARIAN:
            return
    raise AppError(code="FORBIDDEN", message="Staff assignment administration not permitted", status_code=403)


async def create_library(scope: AccessScope, payload: InstitutionLibraryCreate) -> InstitutionLibraryRead:
    await require_facility_manage(scope, institution_level=True)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    code = _norm_code(payload.library_code)
    if await InstitutionLibrary.find_one(Eq(InstitutionLibrary.tenant_id, tenant_id), Eq(InstitutionLibrary.library_code, code)):
        raise AppError(code="CONFLICT", message="Library code exists", status_code=409)
    campus_id = await _assert_campus(tenant_id, payload.campus_id)
    doc = InstitutionLibrary(
        tenant_id=tenant_id,
        library_code=code,
        name=payload.name.strip(),
        description=payload.description,
        campus_id=campus_id,
        address=payload.address,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        operating_status=payload.operating_status,
        updated_by=scope.user_id,
    )
    await doc.insert()
    await _record_history(
        tenant_id,
        actor_id=scope.user_id,
        entity_type=LibraryConfigEntityType.LIBRARY,
        entity_key=code,
        action="create",
        changes=payload.model_dump(mode="json"),
    )
    return _library_read(doc)


async def list_libraries(scope: AccessScope, pagination: Pagination) -> Page[InstitutionLibraryRead]:
    authorize_facility_read(scope)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    allowed = await _assigned_library_codes(scope, tenant_id)
    query = InstitutionLibrary.find(Eq(InstitutionLibrary.tenant_id, tenant_id)).sort("library_code")
    if allowed is not None:
        if not allowed:
            return Page(items=[], total=0, limit=pagination.limit, offset=pagination.offset)
        rows = await query.to_list()
        filtered = [r for r in rows if r.library_code in allowed]
        total = len(filtered)
        page = filtered[pagination.offset : pagination.offset + pagination.limit]
        return Page(items=[_library_read(r) for r in page], total=total, limit=pagination.limit, offset=pagination.offset)
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_library_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def get_library(scope: AccessScope, library_code: str) -> InstitutionLibraryRead:
    tenant_id = await require_facility_read(scope, library_code=library_code)
    doc = await _get_library(tenant_id, library_code)
    return _library_read(doc)


async def update_library(scope: AccessScope, library_code: str, payload: InstitutionLibraryUpdate) -> InstitutionLibraryRead:
    await require_facility_manage(scope, library_code=library_code, institution_level=True)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await _get_library(tenant_id, library_code)
    changes: dict[str, Any] = {}
    if payload.name is not None:
        doc.name = payload.name.strip()
        changes["name"] = doc.name
    if payload.description is not None:
        doc.description = payload.description
        changes["description"] = payload.description
    if payload.campus_id is not None:
        doc.campus_id = await _assert_campus(tenant_id, payload.campus_id)
        changes["campus_id"] = str(doc.campus_id) if doc.campus_id else None
    if payload.address is not None:
        doc.address = payload.address
        changes["address"] = payload.address
    if payload.contact_email is not None:
        doc.contact_email = payload.contact_email
        changes["contact_email"] = payload.contact_email
    if payload.contact_phone is not None:
        doc.contact_phone = payload.contact_phone
        changes["contact_phone"] = payload.contact_phone
    if payload.operating_status is not None:
        doc.operating_status = payload.operating_status
        changes["operating_status"] = payload.operating_status.value
    if payload.is_active is not None:
        doc.is_active = payload.is_active
        changes["is_active"] = payload.is_active
    if not changes:
        raise AppError(code="VALIDATION_ERROR", message="No fields to update", status_code=422)
    doc.updated_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await _record_history(
        tenant_id,
        actor_id=scope.user_id,
        entity_type=LibraryConfigEntityType.LIBRARY,
        entity_key=doc.library_code,
        action="update",
        changes=changes,
    )
    return _library_read(doc)


async def create_branch_facility(scope: AccessScope, payload: LibraryBranchCreate) -> LibraryBranchRead:
    library_code = _norm_code(payload.library_code)
    await require_facility_manage(scope, library_code=library_code, branch_code=None)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    await _get_library(tenant_id, library_code)
    branch_code = _norm_code(payload.branch_code)
    if await LibraryBranch.find_one(Eq(LibraryBranch.tenant_id, tenant_id), Eq(LibraryBranch.branch_code, branch_code)):
        raise AppError(code="CONFLICT", message="Branch code exists", status_code=409)
    campus_id = await _assert_campus(tenant_id, payload.campus_id)
    doc = LibraryBranch(
        tenant_id=tenant_id,
        library_code=library_code,
        branch_code=branch_code,
        name=payload.name.strip(),
        description=payload.description,
        campus_id=campus_id,
        address=payload.address,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        operating_status=payload.operating_status.value,
        updated_by=scope.user_id,
    )
    await doc.insert()
    await _record_history(
        tenant_id,
        actor_id=scope.user_id,
        entity_type=LibraryConfigEntityType.BRANCH,
        entity_key=branch_code,
        action="create",
        changes=payload.model_dump(mode="json"),
    )
    return _branch_read(doc)


async def list_branches(
    scope: AccessScope,
    pagination: Pagination,
    *,
    library_code: str | None = None,
) -> Page[LibraryBranchRead]:
    authorize_facility_read(scope)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    filters: dict[str, Any] = {"tenant_id": tenant_id}
    if library_code:
        filters["library_code"] = _norm_code(library_code)
        await require_facility_read(scope, library_code=library_code)
    allowed = await _assigned_library_codes(scope, tenant_id)
    query = LibraryBranch.find(filters).sort("branch_code")
    rows = await query.to_list()
    if allowed is not None:
        rows = [r for r in rows if r.library_code and r.library_code.upper() in allowed]
    if library_code is None and allowed is not None:
        pass
    total = len(rows)
    page = rows[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=[_branch_read(r) for r in page], total=total, limit=pagination.limit, offset=pagination.offset)


async def get_branch(scope: AccessScope, branch_code: str) -> LibraryBranchRead:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    branch = await _get_branch(tenant_id, branch_code)
    lib_code = branch.library_code or ""
    if lib_code:
        await require_facility_read(scope, library_code=lib_code, branch_code=branch.branch_code)
    else:
        authorize_facility_read(scope)
    return _branch_read(branch)


async def update_branch(scope: AccessScope, branch_code: str, payload: LibraryBranchUpdate) -> LibraryBranchRead:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await _get_branch(tenant_id, branch_code)
    if not doc.library_code:
        await require_facility_manage(scope, institution_level=True)
    else:
        await require_facility_manage(scope, library_code=doc.library_code, branch_code=doc.branch_code)
    changes: dict[str, Any] = {}
    if payload.name is not None:
        doc.name = payload.name.strip()
        changes["name"] = doc.name
    if payload.description is not None:
        doc.description = payload.description
        changes["description"] = payload.description
    if payload.campus_id is not None:
        doc.campus_id = await _assert_campus(tenant_id, payload.campus_id)
        changes["campus_id"] = str(doc.campus_id) if doc.campus_id else None
    if payload.address is not None:
        doc.address = payload.address
        changes["address"] = payload.address
    if payload.contact_email is not None:
        doc.contact_email = payload.contact_email
        changes["contact_email"] = payload.contact_email
    if payload.contact_phone is not None:
        doc.contact_phone = payload.contact_phone
        changes["contact_phone"] = payload.contact_phone
    if payload.operating_status is not None:
        doc.operating_status = payload.operating_status.value
        changes["operating_status"] = payload.operating_status.value
    if payload.is_active is not None:
        doc.is_active = payload.is_active
        changes["is_active"] = payload.is_active
    if not changes:
        raise AppError(code="VALIDATION_ERROR", message="No fields to update", status_code=422)
    doc.updated_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await _record_history(
        tenant_id,
        actor_id=scope.user_id,
        entity_type=LibraryConfigEntityType.BRANCH,
        entity_key=doc.branch_code,
        action="update",
        changes=changes,
    )
    return _branch_read(doc)


async def branch_operational_stats(scope: AccessScope, branch_code: str) -> BranchOperationalStats:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    branch = await _get_branch(tenant_id, branch_code)
    if branch.library_code:
        await require_facility_read(scope, library_code=branch.library_code, branch_code=branch.branch_code)
    else:
        authorize_facility_read(scope)
    copy_rows = await LibraryBookCopyRecord.find(
        Eq(LibraryBookCopyRecord.tenant_id, tenant_id),
        Eq(LibraryBookCopyRecord.branch_code, branch.branch_code),
    ).to_list()
    copy_ids = [c.copy_id for c in copy_rows]
    total = len(copy_ids)
    available = issued = 0
    if copy_ids:
        copies = await LibraryCopy.find({"tenant_id": tenant_id, "copy_id": {"$in": copy_ids}}).to_list()
        for copy in copies:
            if copy.status == LibraryCopyStatus.AVAILABLE:
                available += 1
            elif copy.status == LibraryCopyStatus.ISSUED:
                issued += 1
    active_circ = 0
    if copy_ids:
        active_circ = await LibraryCirculation.find(
            {
                "tenant_id": tenant_id,
                "copy_id": {"$in": copy_ids},
                "status": {"$in": [LibraryCirculationStatus.ACTIVE, LibraryCirculationStatus.OVERDUE]},
            }
        ).count()
    open_fines = await LibraryFine.find(
        Eq(LibraryFine.tenant_id, tenant_id),
        Eq(LibraryFine.status, LibraryFineStatus.OPEN),
    ).count()
    return BranchOperationalStats(
        branch_code=branch.branch_code,
        total_copies=total,
        available_copies=available,
        issued_copies=issued,
        active_circulation=active_circ,
        open_fines=open_fines,
    )


async def upsert_operating_hours(scope: AccessScope, payload: OperatingHoursUpsert) -> OperatingHoursRead:
    library_code = _norm_code(payload.library_code)
    branch_code = _norm_code(payload.branch_code) if payload.branch_code else None
    await require_facility_manage(scope, library_code=library_code, branch_code=branch_code)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    await _get_library(tenant_id, library_code)
    if branch_code:
        branch = await _get_branch(tenant_id, branch_code)
        await _assert_branch_belongs_to_library(branch, library_code)
    validate_operating_days(payload.days)
    doc = await LibraryOperatingHours.find_one(
        {"tenant_id": tenant_id, "library_code": library_code, "branch_code": branch_code},
    )
    if doc is None:
        doc = LibraryOperatingHours(
            tenant_id=tenant_id,
            library_code=library_code,
            branch_code=branch_code,
            days=payload.days,
            updated_by=scope.user_id,
        )
        await doc.insert()
        action = "create"
    else:
        doc.days = payload.days
        doc.updated_by = scope.user_id
        doc.updated_at = utcnow()
        await doc.save()
        action = "update"
    key = f"{library_code}:{branch_code or 'ALL'}"
    await _record_history(
        tenant_id,
        actor_id=scope.user_id,
        entity_type=LibraryConfigEntityType.OPERATING_HOURS,
        entity_key=key,
        action=action,
        changes={"days": [d.model_dump() for d in payload.days]},
    )
    return OperatingHoursRead(library_code=library_code, branch_code=branch_code, days=doc.days, updated_at=doc.updated_at)


async def get_operating_hours(
    scope: AccessScope,
    *,
    library_code: str,
    branch_code: str | None = None,
) -> OperatingHoursRead:
    library_code = _norm_code(library_code)
    branch_code = _norm_code(branch_code) if branch_code else None
    tenant_id = await require_facility_read(scope, library_code=library_code, branch_code=branch_code)
    doc = await LibraryOperatingHours.find_one(
        {"tenant_id": tenant_id, "library_code": library_code, "branch_code": branch_code},
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Operating hours not configured", status_code=404)
    return OperatingHoursRead(library_code=library_code, branch_code=branch_code, days=doc.days, updated_at=doc.updated_at)


async def create_holiday(scope: AccessScope, payload: LibraryHolidayCreate) -> LibraryHolidayRead:
    library_code = _norm_code(payload.library_code)
    branch_code = _norm_code(payload.branch_code) if payload.branch_code else None
    await require_facility_manage(scope, library_code=library_code, branch_code=branch_code)
    validate_holiday_range(payload.start_date, payload.end_date)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    await _get_library(tenant_id, library_code)
    if branch_code:
        branch = await _get_branch(tenant_id, branch_code)
        await _assert_branch_belongs_to_library(branch, library_code)
    if await LibraryHoliday.find_one(Eq(LibraryHoliday.tenant_id, tenant_id), Eq(LibraryHoliday.holiday_id, payload.holiday_id)):
        raise AppError(code="CONFLICT", message="Holiday id exists", status_code=409)
    doc = LibraryHoliday(
        tenant_id=tenant_id,
        holiday_id=payload.holiday_id.strip(),
        library_code=library_code,
        branch_code=branch_code,
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason=payload.reason.strip(),
        updated_by=scope.user_id,
    )
    await doc.insert()
    await _record_history(
        tenant_id,
        actor_id=scope.user_id,
        entity_type=LibraryConfigEntityType.HOLIDAY,
        entity_key=doc.holiday_id,
        action="create",
        changes=payload.model_dump(mode="json"),
    )
    return _holiday_read(doc)


def _holiday_read(doc: LibraryHoliday) -> LibraryHolidayRead:
    return LibraryHolidayRead(
        holiday_id=doc.holiday_id,
        library_code=doc.library_code,
        branch_code=doc.branch_code,
        start_date=doc.start_date,
        end_date=doc.end_date,
        reason=doc.reason,
        is_active=doc.is_active,
        updated_at=doc.updated_at,
    )


async def update_holiday(scope: AccessScope, holiday_id: str, payload: LibraryHolidayUpdate) -> LibraryHolidayRead:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await LibraryHoliday.find_one(Eq(LibraryHoliday.tenant_id, tenant_id), Eq(LibraryHoliday.holiday_id, holiday_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Holiday not found", status_code=404)
    await require_facility_manage(scope, library_code=doc.library_code, branch_code=doc.branch_code)
    changes: dict[str, Any] = {}
    start = payload.start_date or doc.start_date
    end = payload.end_date or doc.end_date
    validate_holiday_range(start, end)
    if payload.start_date is not None:
        doc.start_date = payload.start_date
        changes["start_date"] = payload.start_date.isoformat()
    if payload.end_date is not None:
        doc.end_date = payload.end_date
        changes["end_date"] = payload.end_date.isoformat()
    if payload.reason is not None:
        doc.reason = payload.reason.strip()
        changes["reason"] = doc.reason
    if payload.is_active is not None:
        doc.is_active = payload.is_active
        changes["is_active"] = payload.is_active
    if not changes:
        raise AppError(code="VALIDATION_ERROR", message="No fields to update", status_code=422)
    doc.updated_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await _record_history(
        tenant_id,
        actor_id=scope.user_id,
        entity_type=LibraryConfigEntityType.HOLIDAY,
        entity_key=doc.holiday_id,
        action="update",
        changes=changes,
    )
    return _holiday_read(doc)


async def list_holidays(
    scope: AccessScope,
    pagination: Pagination,
    *,
    library_code: str | None = None,
    branch_code: str | None = None,
    active_only: bool = True,
) -> Page[LibraryHolidayRead]:
    authorize_facility_read(scope)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    filters: dict[str, Any] = {"tenant_id": tenant_id}
    if library_code:
        lib = _norm_code(library_code)
        filters["library_code"] = lib
        await require_facility_read(scope, library_code=lib, branch_code=branch_code)
    if branch_code:
        filters["branch_code"] = _norm_code(branch_code)
    if active_only:
        filters["is_active"] = True
    query = LibraryHoliday.find(filters).sort("-start_date")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_holiday_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def get_holiday(scope: AccessScope, holiday_id: str) -> LibraryHolidayRead:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await LibraryHoliday.find_one(Eq(LibraryHoliday.tenant_id, tenant_id), Eq(LibraryHoliday.holiday_id, holiday_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Holiday not found", status_code=404)
    await require_facility_read(scope, library_code=doc.library_code, branch_code=doc.branch_code)
    return _holiday_read(doc)


async def create_staff_assignment(scope: AccessScope, payload: LibraryStaffAssignmentCreate) -> LibraryStaffAssignmentRead:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    library_code = _norm_code(payload.library_code)
    await require_staff_assignment_admin(scope, tenant_id, library_code)
    branch_code = _norm_code(payload.branch_code) if payload.branch_code else None
    await _get_library(tenant_id, library_code)
    if branch_code:
        branch = await _get_branch(tenant_id, branch_code)
        await _assert_branch_belongs_to_library(branch, library_code)
    employee_id = to_object_id(payload.employee_user_id, "employee_user_id")
    employee = await EmployeeRecord.find_one(
        Eq(EmployeeRecord.tenant_id, tenant_id),
        Eq(EmployeeRecord.user_id, employee_id),
    )
    if employee is None:
        raise AppError(code="VALIDATION_ERROR", message="Employee record not found", status_code=422)
    if employee.employment_status != FacultyEmploymentStatus.ACTIVE:
        raise AppError(code="VALIDATION_ERROR", message="Employee is not active", status_code=422)
    if await LibraryStaffAssignment.find_one(
        Eq(LibraryStaffAssignment.tenant_id, tenant_id),
        Eq(LibraryStaffAssignment.assignment_id, payload.assignment_id),
    ):
        raise AppError(code="CONFLICT", message="Assignment id exists", status_code=409)
    doc = LibraryStaffAssignment(
        tenant_id=tenant_id,
        assignment_id=payload.assignment_id.strip(),
        employee_user_id=employee_id,
        library_code=library_code,
        branch_code=branch_code,
        staff_role=payload.staff_role,
        assigned_on=payload.assigned_on,
        notes=payload.notes,
        updated_by=scope.user_id,
    )
    await doc.insert()
    await _record_history(
        tenant_id,
        actor_id=scope.user_id,
        entity_type=LibraryConfigEntityType.STAFF_ASSIGNMENT,
        entity_key=doc.assignment_id,
        action="create",
        changes=payload.model_dump(mode="json"),
    )
    return _staff_read(doc)


def _staff_read(doc: LibraryStaffAssignment) -> LibraryStaffAssignmentRead:
    return LibraryStaffAssignmentRead(
        assignment_id=doc.assignment_id,
        employee_user_id=str(doc.employee_user_id),
        library_code=doc.library_code,
        branch_code=doc.branch_code,
        staff_role=doc.staff_role,
        assigned_on=doc.assigned_on,
        status=doc.status,
        notes=doc.notes,
        updated_at=doc.updated_at,
    )


async def update_staff_assignment(
    scope: AccessScope,
    assignment_id: str,
    payload: LibraryStaffAssignmentUpdate,
) -> LibraryStaffAssignmentRead:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await LibraryStaffAssignment.find_one(
        Eq(LibraryStaffAssignment.tenant_id, tenant_id),
        Eq(LibraryStaffAssignment.assignment_id, assignment_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Staff assignment not found", status_code=404)
    await require_staff_assignment_admin(scope, tenant_id, doc.library_code)
    changes: dict[str, Any] = {}
    if payload.branch_code is not None:
        branch_code = _norm_code(payload.branch_code)
        branch = await _get_branch(tenant_id, branch_code)
        await _assert_branch_belongs_to_library(branch, doc.library_code)
        doc.branch_code = branch_code
        changes["branch_code"] = branch_code
    if payload.staff_role is not None:
        doc.staff_role = payload.staff_role
        changes["staff_role"] = payload.staff_role.value
    if payload.status is not None:
        doc.status = payload.status
        changes["status"] = payload.status.value
    if payload.notes is not None:
        doc.notes = payload.notes
        changes["notes"] = payload.notes
    if not changes:
        raise AppError(code="VALIDATION_ERROR", message="No fields to update", status_code=422)
    doc.updated_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await _record_history(
        tenant_id,
        actor_id=scope.user_id,
        entity_type=LibraryConfigEntityType.STAFF_ASSIGNMENT,
        entity_key=doc.assignment_id,
        action="update",
        changes=changes,
    )
    return _staff_read(doc)


async def list_staff_assignments(
    scope: AccessScope,
    pagination: Pagination,
    *,
    library_code: str | None = None,
    branch_code: str | None = None,
) -> Page[LibraryStaffAssignmentRead]:
    authorize_facility_read(scope)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    filters: dict[str, Any] = {"tenant_id": tenant_id}
    if library_code:
        lib = _norm_code(library_code)
        filters["library_code"] = lib
        await require_facility_read(scope, library_code=lib, branch_code=branch_code)
    if branch_code:
        filters["branch_code"] = _norm_code(branch_code)
    rows = await LibraryStaffAssignment.find(filters).sort("-updated_at").to_list()
    total = len(rows)
    page = rows[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=[_staff_read(r) for r in page], total=total, limit=pagination.limit, offset=pagination.offset)


async def create_section(scope: AccessScope, payload: LibrarySectionCreate) -> LibrarySectionRead:
    branch_code = _norm_code(payload.branch_code)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    branch = await _get_branch(tenant_id, branch_code)
    if not branch.library_code:
        await require_facility_manage(scope, institution_level=True)
    else:
        await require_facility_manage(scope, library_code=branch.library_code, branch_code=branch_code)
    section_code = payload.section_code.strip().upper()
    if await LibrarySection.find_one(
        Eq(LibrarySection.tenant_id, tenant_id),
        Eq(LibrarySection.branch_code, branch_code),
        Eq(LibrarySection.section_code, section_code),
    ):
        raise AppError(code="CONFLICT", message="Section code exists", status_code=409)
    doc = LibrarySection(
        tenant_id=tenant_id,
        branch_code=branch_code,
        section_code=section_code,
        name=payload.name.strip(),
        description=payload.description,
        updated_by=scope.user_id,
    )
    await doc.insert()
    await _record_history(
        tenant_id,
        actor_id=scope.user_id,
        entity_type=LibraryConfigEntityType.SECTION,
        entity_key=f"{branch_code}:{section_code}",
        action="create",
        changes=payload.model_dump(mode="json"),
    )
    return _section_read(doc)


def _section_read(doc: LibrarySection) -> LibrarySectionRead:
    return LibrarySectionRead(
        branch_code=doc.branch_code,
        section_code=doc.section_code,
        name=doc.name,
        description=doc.description,
        is_active=doc.is_active,
        updated_at=doc.updated_at,
    )


async def update_section(scope: AccessScope, branch_code: str, section_code: str, payload: LibrarySectionUpdate) -> LibrarySectionRead:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    branch_code = _norm_code(branch_code)
    section_code = section_code.strip().upper()
    doc = await LibrarySection.find_one(
        Eq(LibrarySection.tenant_id, tenant_id),
        Eq(LibrarySection.branch_code, branch_code),
        Eq(LibrarySection.section_code, section_code),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Section not found", status_code=404)
    branch = await _get_branch(tenant_id, branch_code)
    if branch.library_code:
        await require_facility_manage(scope, library_code=branch.library_code, branch_code=branch_code)
    else:
        await require_facility_manage(scope, institution_level=True)
    changes: dict[str, Any] = {}
    if payload.name is not None:
        doc.name = payload.name.strip()
        changes["name"] = doc.name
    if payload.description is not None:
        doc.description = payload.description
        changes["description"] = payload.description
    if payload.is_active is not None:
        doc.is_active = payload.is_active
        changes["is_active"] = payload.is_active
    if not changes:
        raise AppError(code="VALIDATION_ERROR", message="No fields to update", status_code=422)
    doc.updated_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await _record_history(
        tenant_id,
        actor_id=scope.user_id,
        entity_type=LibraryConfigEntityType.SECTION,
        entity_key=f"{branch_code}:{section_code}",
        action="update",
        changes=changes,
    )
    return _section_read(doc)


async def list_sections(
    scope: AccessScope,
    pagination: Pagination,
    *,
    branch_code: str,
) -> Page[LibrarySectionRead]:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    branch_code = _norm_code(branch_code)
    branch = await _get_branch(tenant_id, branch_code)
    if branch.library_code:
        await require_facility_read(scope, library_code=branch.library_code, branch_code=branch_code)
    else:
        authorize_facility_read(scope)
    query = LibrarySection.find(
        Eq(LibrarySection.tenant_id, tenant_id),
        Eq(LibrarySection.branch_code, branch_code),
    ).sort("section_code")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_section_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def create_shelf_location(scope: AccessScope, payload: LibraryShelfLocationCreate) -> LibraryShelfLocationRead:
    branch_code = _norm_code(payload.branch_code)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    branch = await _get_branch(tenant_id, branch_code)
    if branch.library_code:
        await require_facility_manage(scope, library_code=branch.library_code, branch_code=branch_code)
    else:
        await require_facility_manage(scope, institution_level=True)
    location_code = payload.location_code.strip().upper()
    if await LibraryShelfLocation.find_one(
        Eq(LibraryShelfLocation.tenant_id, tenant_id),
        Eq(LibraryShelfLocation.branch_code, branch_code),
        Eq(LibraryShelfLocation.location_code, location_code),
    ):
        raise AppError(code="CONFLICT", message="Location code exists", status_code=409)
    parent_level = None
    if payload.parent_location_code:
        parent = await LibraryShelfLocation.find_one(
            Eq(LibraryShelfLocation.tenant_id, tenant_id),
            Eq(LibraryShelfLocation.branch_code, branch_code),
            Eq(LibraryShelfLocation.location_code, payload.parent_location_code.strip().upper()),
        )
        if parent is None:
            raise AppError(code="VALIDATION_ERROR", message="Parent location not found", status_code=422)
        parent_level = parent.level
    validate_location_parent(payload.level, parent_level)
    doc = LibraryShelfLocation(
        tenant_id=tenant_id,
        branch_code=branch_code,
        location_code=location_code,
        parent_location_code=payload.parent_location_code.strip().upper() if payload.parent_location_code else None,
        level=payload.level,
        name=payload.name.strip(),
        description=payload.description,
        updated_by=scope.user_id,
    )
    await doc.insert()
    await _record_history(
        tenant_id,
        actor_id=scope.user_id,
        entity_type=LibraryConfigEntityType.SHELF_LOCATION,
        entity_key=f"{branch_code}:{location_code}",
        action="create",
        changes=payload.model_dump(mode="json"),
    )
    return _location_read(doc)


def _location_read(doc: LibraryShelfLocation) -> LibraryShelfLocationRead:
    return LibraryShelfLocationRead(
        branch_code=doc.branch_code,
        location_code=doc.location_code,
        parent_location_code=doc.parent_location_code,
        level=doc.level,
        name=doc.name,
        description=doc.description,
        is_active=doc.is_active,
        updated_at=doc.updated_at,
    )


async def update_shelf_location(
    scope: AccessScope,
    branch_code: str,
    location_code: str,
    payload: LibraryShelfLocationUpdate,
) -> LibraryShelfLocationRead:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    branch_code = _norm_code(branch_code)
    location_code = location_code.strip().upper()
    doc = await LibraryShelfLocation.find_one(
        Eq(LibraryShelfLocation.tenant_id, tenant_id),
        Eq(LibraryShelfLocation.branch_code, branch_code),
        Eq(LibraryShelfLocation.location_code, location_code),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Shelf location not found", status_code=404)
    branch = await _get_branch(tenant_id, branch_code)
    if branch.library_code:
        await require_facility_manage(scope, library_code=branch.library_code, branch_code=branch_code)
    else:
        await require_facility_manage(scope, institution_level=True)
    changes: dict[str, Any] = {}
    if payload.name is not None:
        doc.name = payload.name.strip()
        changes["name"] = doc.name
    if payload.description is not None:
        doc.description = payload.description
        changes["description"] = payload.description
    if payload.is_active is not None:
        doc.is_active = payload.is_active
        changes["is_active"] = payload.is_active
    if not changes:
        raise AppError(code="VALIDATION_ERROR", message="No fields to update", status_code=422)
    doc.updated_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    await _record_history(
        tenant_id,
        actor_id=scope.user_id,
        entity_type=LibraryConfigEntityType.SHELF_LOCATION,
        entity_key=f"{branch_code}:{location_code}",
        action="update",
        changes=changes,
    )
    return _location_read(doc)


async def list_shelf_locations(
    scope: AccessScope,
    pagination: Pagination,
    *,
    branch_code: str,
) -> Page[LibraryShelfLocationRead]:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    branch_code = _norm_code(branch_code)
    branch = await _get_branch(tenant_id, branch_code)
    if branch.library_code:
        await require_facility_read(scope, library_code=branch.library_code, branch_code=branch_code)
    else:
        authorize_facility_read(scope)
    query = LibraryShelfLocation.find(
        Eq(LibraryShelfLocation.tenant_id, tenant_id),
        Eq(LibraryShelfLocation.branch_code, branch_code),
    ).sort("location_code")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_location_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def list_configuration_history(
    scope: AccessScope,
    pagination: Pagination,
    *,
    entity_type: LibraryConfigEntityType | None = None,
    entity_key: str | None = None,
) -> Page[LibraryConfigurationHistoryRead]:
    authorize_facility_read(scope)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    filters: dict[str, Any] = {"tenant_id": tenant_id}
    if entity_type is not None:
        filters["entity_type"] = entity_type
    if entity_key is not None:
        filters["entity_key"] = entity_key
    query = LibraryConfigurationHistory.find(filters).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        LibraryConfigurationHistoryRead(
            entity_type=r.entity_type.value,
            entity_key=r.entity_key,
            action=r.action,
            actor_id=str(r.actor_id) if r.actor_id else None,
            changes=r.changes,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)